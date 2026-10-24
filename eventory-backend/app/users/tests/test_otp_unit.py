"""Unit tests for the cache-backed OTP lifecycle."""

from __future__ import annotations

import re
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import override_settings

from app.core.exceptions import (
    BadRequestError,
    GoneError,
    ServiceUnavailableError,
    TooManyRequestsError,
)
from app.users.services.otp import (
    PURPOSE_PASSWORD_RESET,
    PURPOSE_SIGNUP,
    _delivery_key,
    _digest,
    issue_otp,
    verify_key,
    verify_otp,
)


@pytest.mark.parametrize("length", [4, 6, 8])
def test_generate_otp_returns_numeric_string_of_requested_length(length):
    from app.users.services.otp import generate_otp

    code = generate_otp(length)

    assert len(code) == length
    assert code.isdigit()


def test_issue_otp_stores_digest_and_short_lived_delivery_code():
    with override_settings(
        OTP_LENGTH=6,
        OTP_TTL_SECONDS=180,
        OTP_RESEND_COOLDOWN_SECONDS=30,
        OTP_DELIVERY_TTL_SECONDS=60,
        SECRET_KEY="otp-unit-test-secret",
    ):
        issued = issue_otp(
            purpose=PURPOSE_SIGNUP,
            channel="phone",
            identifier="+989121234567",
            extra={"username": "tester"},
        )

        record = cache.get(issued["verify_key"])
        delivery_code = cache.get(issued["delivery_key"])

        assert issued["expires_in"] == 180
        assert record["attempts"] == 0
        assert record["extra"] == {"username": "tester"}
        assert record["digest"] == _digest(delivery_code)
        assert record["digest"] != delivery_code
        assert re.fullmatch(r"\d{6}", delivery_code)


def test_issue_otp_rejects_request_during_resend_cooldown():
    kwargs = {
        "purpose": PURPOSE_SIGNUP,
        "channel": "email",
        "identifier": "tester@example.com",
    }

    issue_otp(**kwargs)

    with pytest.raises(TooManyRequestsError):
        issue_otp(**kwargs)


def test_verify_otp_consumes_valid_code_and_delivery_payload():
    issued = issue_otp(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
    )
    code = cache.get(issued["delivery_key"])

    record = verify_otp(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
        otp=code,
    )

    assert record["purpose"] == PURPOSE_SIGNUP
    assert cache.get(issued["verify_key"]) is None
    assert cache.get(issued["delivery_key"]) is None


def test_verify_otp_rejects_incorrect_code_and_increments_attempts():
    issued = issue_otp(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
    )

    actual_code = cache.get(issued["delivery_key"])
    wrong_code = "000000" if actual_code != "000000" else "000001"
    with pytest.raises(BadRequestError):
        verify_otp(
            purpose=PURPOSE_SIGNUP,
            channel="phone",
            identifier="+989121234567",
            otp=wrong_code,
        )

    record = cache.get(issued["verify_key"])
    assert record["attempts"] == 1


def test_verify_otp_deletes_record_after_maximum_failed_attempts():
    with override_settings(OTP_MAX_ATTEMPTS=3):
        issued = issue_otp(
            purpose=PURPOSE_SIGNUP,
            channel="phone",
            identifier="+989121234567",
        )

        actual_code = cache.get(issued["delivery_key"])
        wrong_code = "000000" if actual_code != "000000" else "000001"
        for _ in range(2):
            with pytest.raises(BadRequestError):
                verify_otp(
                    purpose=PURPOSE_SIGNUP,
                    channel="phone",
                    identifier="+989121234567",
                    otp=wrong_code,
                )

        with pytest.raises(TooManyRequestsError):
            verify_otp(
                purpose=PURPOSE_SIGNUP,
                channel="phone",
                identifier="+989121234567",
                otp=wrong_code,
            )

        assert cache.get(issued["verify_key"]) is None


def test_verify_otp_raises_gone_when_record_is_missing_or_expired():
    with pytest.raises(GoneError):
        verify_otp(
            purpose=PURPOSE_SIGNUP,
            channel="phone",
            identifier="+989121234567",
            otp="123456",
        )


def test_signup_otp_cannot_be_used_for_password_reset():
    issued = issue_otp(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
    )
    code = cache.get(issued["delivery_key"])

    with pytest.raises(GoneError):
        verify_otp(
            purpose=PURPOSE_PASSWORD_RESET,
            channel="phone",
            identifier="+989121234567",
            otp=code,
        )


def test_issue_otp_maps_cache_failure_to_service_unavailable():
    with patch("app.users.services.otp.cache.add", side_effect=RuntimeError("cache down")):
        with pytest.raises(ServiceUnavailableError):
            issue_otp(
                purpose=PURPOSE_SIGNUP,
                channel="phone",
                identifier="+989121234567",
            )


def test_verify_key_and_delivery_key_are_scoped_by_purpose_and_identifier():
    signup_key = verify_key(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
    )
    reset_key = verify_key(
        purpose=PURPOSE_PASSWORD_RESET,
        channel="phone",
        identifier="+989121234567",
    )
    delivery_key = _delivery_key(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
    )

    assert signup_key != reset_key
    assert delivery_key != signup_key
