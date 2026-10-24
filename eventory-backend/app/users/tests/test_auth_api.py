"""HTTP-level integration/E2E tests for the public authentication API."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from django.core.cache import cache
from rest_framework import status

from app.users.models import User
from app.users.services.otp import PURPOSE_PASSWORD_RESET, PURPOSE_SIGNUP, _delivery_key


@pytest.mark.django_db
def test_signup_and_verify_otp_returns_tokens_and_creates_user(api_client, monkeypatch):
    monkeypatch.setattr("app.users.services.auth.deliver_message.delay", Mock())
    signup_payload = {
        "channel": "phone",
        "phone": "09121234567",
        "username": "Test User",
        "last_name": "Tester",
        "password": "StrongPass1!",
    }

    signup_response = api_client.post("/api/auth/signup/", signup_payload, format="json")

    assert signup_response.status_code == status.HTTP_202_ACCEPTED
    assert signup_response.data["identifier"] == "+989121234567"
    assert not User.objects.filter(phone="+989121234567").exists()

    delivery_key = _delivery_key(
        purpose=PURPOSE_SIGNUP,
        channel="phone",
        identifier="+989121234567",
    )
    otp = cache.get(delivery_key)
    assert otp is not None

    verify_response = api_client.post(
        "/api/auth/verify/",
        {
            "channel": "phone",
            "identifier": "+989121234567",
            "otp": otp,
        },
        format="json",
    )

    assert verify_response.status_code == status.HTTP_200_OK
    assert verify_response.data["access"]
    assert verify_response.data["refresh"]
    user = User.objects.get(phone="+989121234567")
    assert user.is_phone_verified is True
    assert hasattr(user, "wallet")
    # Regression assertion: signup must preserve the user's chosen raw password.
    # This catches accidental double-hashing in the signup creation pipeline.
    assert user.check_password("StrongPass1!")


@pytest.mark.django_db
def test_signup_verify_rejects_wrong_otp(api_client, monkeypatch):
    monkeypatch.setattr("app.users.services.auth.deliver_message.delay", Mock())
    api_client.post(
        "/api/auth/signup/",
        {
            "channel": "phone",
            "phone": "09121234567",
            "username": "Test User",
            "last_name": "Tester",
            "password": "StrongPass1!",
        },
        format="json",
    )

    real_code = cache.get(
        _delivery_key(
            purpose=PURPOSE_SIGNUP,
            channel="phone",
            identifier="+989121234567",
        )
    )
    wrong_code = "000000" if real_code != "000000" else "000001"
    response = api_client.post(
        "/api/auth/verify/",
        {
            "channel": "phone",
            "identifier": "+989121234567",
            "otp": wrong_code,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(phone="+989121234567").exists()


@pytest.mark.django_db
def test_login_api_accepts_valid_credentials(api_client, verified_phone_user):
    response = api_client.post(
        "/api/auth/login/",
        {
            "channel": "phone",
            "identifier": verified_phone_user.phone,
            "password": "StrongPass1!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["access"]
    assert response.data["refresh"]
    assert response.data["user"]["id"] == verified_phone_user.pk


@pytest.mark.django_db
def test_login_api_rejects_wrong_password(api_client, verified_phone_user):
    response = api_client.post(
        "/api/auth/login/",
        {
            "channel": "phone",
            "identifier": verified_phone_user.phone,
            "password": "WrongPassword1!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error_code"] == "invalid_credentials"


@pytest.mark.django_db
def test_password_reset_api_request_confirm_and_login(api_client, verified_phone_user, monkeypatch):
    monkeypatch.setattr("app.users.services.auth.deliver_message.delay", Mock())
    request_response = api_client.post(
        "/api/auth/password-reset/",
        {"channel": "phone", "identifier": verified_phone_user.phone},
        format="json",
    )

    assert request_response.status_code == status.HTTP_200_OK
    assert "If an account exists" in request_response.data["message"]

    delivery_key = _delivery_key(
        purpose=PURPOSE_PASSWORD_RESET,
        channel="phone",
        identifier=verified_phone_user.phone,
    )
    otp = cache.get(delivery_key)
    assert otp is not None
    new_password = "ACompletelyNew9!"

    confirm_response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {
            "channel": "phone",
            "identifier": verified_phone_user.phone,
            "otp": otp,
            "new_password": new_password,
        },
        format="json",
    )

    assert confirm_response.status_code == status.HTTP_200_OK
    verified_phone_user.refresh_from_db()
    assert verified_phone_user.check_password(new_password)

    login_response = api_client.post(
        "/api/auth/login/",
        {
            "channel": "phone",
            "identifier": verified_phone_user.phone,
            "password": new_password,
        },
        format="json",
    )
    assert login_response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_password_reset_confirm_returns_gone_for_missing_otp(api_client, verified_phone_user):
    response = api_client.post(
        "/api/auth/password-reset/confirm/",
        {
            "channel": "phone",
            "identifier": verified_phone_user.phone,
            "otp": "123456",
            "new_password": "ACompletelyNew9!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_410_GONE
    assert response.data["error_code"] == "otp_expired"
    verified_phone_user.refresh_from_db()
    assert verified_phone_user.check_password("StrongPass1!")


@pytest.mark.django_db
def test_password_reset_otp_cannot_be_reused(api_client, verified_phone_user, monkeypatch):
    monkeypatch.setattr("app.users.services.auth.deliver_message.delay", Mock())
    api_client.post(
        "/api/auth/password-reset/",
        {"channel": "phone", "identifier": verified_phone_user.phone},
        format="json",
    )
    delivery_key = _delivery_key(
        purpose=PURPOSE_PASSWORD_RESET,
        channel="phone",
        identifier=verified_phone_user.phone,
    )
    otp = cache.get(delivery_key)
    payload = {
        "channel": "phone",
        "identifier": verified_phone_user.phone,
        "otp": otp,
        "new_password": "ACompletelyNew9!",
    }

    first_response = api_client.post(
        "/api/auth/password-reset/confirm/", payload, format="json"
    )
    second_response = api_client.post(
        "/api/auth/password-reset/confirm/", payload, format="json"
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_410_GONE

@pytest.mark.django_db
def test_admin_users_endpoint_requires_authentication(api_client):
    response = api_client.get("/api/admin/users/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
