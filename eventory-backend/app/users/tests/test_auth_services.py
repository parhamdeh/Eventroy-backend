"""Tests for authentication service behavior and side effects."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from django.core.cache import cache

from app.core.exceptions import InvalidCredentialsError
from app.users.models import User
from app.users.services import auth
from app.users.services.otp import PURPOSE_PASSWORD_RESET, _delivery_key


@pytest.mark.django_db
def test_login_returns_tokens_for_verified_user(verified_phone_user):
    result = auth.login_with_password(
        channel="phone",
        identifier=verified_phone_user.phone,
        password="StrongPass1!",
    )

    assert result["user"].pk == verified_phone_user.pk
    assert result["access"]
    assert result["refresh"]


@pytest.mark.django_db
def test_login_rejects_incorrect_password(verified_phone_user):
    with pytest.raises(InvalidCredentialsError):
        auth.login_with_password(
            channel="phone",
            identifier=verified_phone_user.phone,
            password="IncorrectPass1!",
        )


@pytest.mark.django_db
def test_login_rejects_unverified_phone():
    user = User.objects.create_user(
        phone="+989121234568",
        password="StrongPass1!",
        username="Unverified",
        last_name="User",
        is_phone_verified=False,
    )

    with pytest.raises(InvalidCredentialsError):
        auth.login_with_password(
            channel="phone",
            identifier=user.phone,
            password="StrongPass1!",
        )

@pytest.mark.django_db
def test_password_reset_for_unknown_identifier_returns_generic_response(monkeypatch):
    queue = Mock()
    monkeypatch.setattr(auth.deliver_message, "delay", queue)

    response = auth.request_password_reset(
        channel="phone",
        identifier="+989121234569",
    )

    assert "If an account exists" in response["message"]
    queue.assert_not_called()


@pytest.mark.django_db
def test_password_reset_request_issues_otp_for_verified_user(
    verified_phone_user, monkeypatch
):
    queue = Mock()
    monkeypatch.setattr(auth.deliver_message, "delay", queue)

    response = auth.request_password_reset(
        channel="phone",
        identifier=verified_phone_user.phone,
    )
    delivery_key = _delivery_key(
        purpose=PURPOSE_PASSWORD_RESET,
        channel="phone",
        identifier=verified_phone_user.phone,
    )

    assert "If an account exists" in response["message"]
    assert cache.get(delivery_key) is not None
    queue.assert_called_once()
    queued_kwargs = queue.call_args.kwargs
    assert queued_kwargs["recipient"] == verified_phone_user.phone
    assert "code" not in queued_kwargs.get("context", {})
    assert queued_kwargs["context"]["delivery_key"] == delivery_key


@pytest.mark.django_db
def test_password_reset_changes_password_and_allows_login(
    verified_phone_user, monkeypatch
):
    queue = Mock()
    monkeypatch.setattr(auth.deliver_message, "delay", queue)
    auth.request_password_reset(
        channel="phone",
        identifier=verified_phone_user.phone,
    )
    delivery_key = _delivery_key(
        purpose=PURPOSE_PASSWORD_RESET,
        channel="phone",
        identifier=verified_phone_user.phone,
    )
    otp = cache.get(delivery_key)
    new_password = "ACompletelyNew9!"

    result = auth.confirm_password_reset(
        channel="phone",
        identifier=verified_phone_user.phone,
        otp=otp,
        new_password=new_password,
    )

    verified_phone_user.refresh_from_db()
    assert "reset" in result["message"].lower()
    assert verified_phone_user.check_password(new_password)
    assert cache.get(delivery_key) is None

    login_result = auth.login_with_password(
        channel="phone",
        identifier=verified_phone_user.phone,
        password=new_password,
    )
    assert login_result["user"].pk == verified_phone_user.pk


@pytest.mark.django_db
def test_password_reset_with_wrong_otp_does_not_change_password(
    verified_phone_user, monkeypatch
):
    monkeypatch.setattr(auth.deliver_message, "delay", Mock())
    auth.request_password_reset(
        channel="phone",
        identifier=verified_phone_user.phone,
    )

    real_code = cache.get(
        _delivery_key(
            purpose=PURPOSE_PASSWORD_RESET,
            channel="phone",
            identifier=verified_phone_user.phone,
        )
    )
    wrong_code = "000000" if real_code != "000000" else "000001"
    from app.core.exceptions import BadRequestError

    with pytest.raises(BadRequestError):
        auth.confirm_password_reset(
            channel="phone",
            identifier=verified_phone_user.phone,
            otp=wrong_code,
            new_password="ACompletelyNew9!",
        )

    verified_phone_user.refresh_from_db()
    assert verified_phone_user.check_password("StrongPass1!")
