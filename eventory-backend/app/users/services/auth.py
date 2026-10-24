"""Authentication workflows: signup, OTP verify, login, password reset, Google."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from datetime import date

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from app.core.exceptions import (
    AlreadyExistsError,
    InvalidCredentialsError,
    UnauthorizedError,
    ValidationFailedError,
)
from app.sms_gateway.content import OTP_EMAIL_TEMPLATE, OTP_SMS_TEMPLATE
from app.sms_gateway.tasks import deliver_message
from app.users.identifiers import normalize_email, normalize_identifier, normalize_phone
from app.users.models import User
from app.users.selectors.users import (
    user_get_by_email,
    user_get_by_google_sub,
    user_get_by_phone,
    user_get_for_login,
)
from app.users.services.otp import (
    PURPOSE_PASSWORD_RESET,
    PURPOSE_SIGNUP,
    issue_otp,
    verify_otp,
)
from app.users.services.tokens import blacklist_user_refresh_tokens, issue_tokens_for_user
from app.users.services.users import create_user

logger = logging.getLogger(__name__)

_GENERIC_RESET_MESSAGE = _("If an account exists, a verification code was sent.")
_GENERIC_LOGIN_ERROR = InvalidCredentialsError


def _queue_otp(*, channel: str, identifier: str, delivery_key: str, purpose: str) -> None:
    """Queue OTP delivery without putting the code in the Celery signature."""
    template = OTP_SMS_TEMPLATE if channel == "phone" else OTP_EMAIL_TEMPLATE
    deliver_message.delay(
        channel=channel,
        recipient=identifier,
        template=template,
        context={"delivery_key": delivery_key},
        idempotency_key=None,
    )


def _auth_payload(user: User) -> dict[str, Any]:
    tokens = issue_tokens_for_user(user)
    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": user,
    }


def register_user(
    *,
    channel: str,
    phone: str,
    password: str,
    username: str,
    last_name: str,
    email: str = "",
    birth_date: Any = None,
) -> dict[str, Any]:
    """
    Validate registration data, store a pending profile in cache, and send an OTP.

    A User row is not created until the OTP is verified.
    """

    channel = channel.strip().lower()
    phone = normalize_phone(phone)
    email = normalize_email(email) if email else ""
    if channel == "email" and not email:
        raise ValidationFailedError(_("Email is required when registering with email."))

    identifier = phone if channel == "phone" else email

    if user_get_by_phone(phone=phone):
        raise AlreadyExistsError(_("An account with this phone number already exists."))
    if email and user_get_by_email(email=email):
        raise AlreadyExistsError(_("An account with this email already exists."))

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise ValidationFailedError(
            _("Validation error."),
            extra={"password": list(exc.messages)},
        ) from exc

    extra = {
        "phone": phone,
        "email": email,
        "username": username.strip(),
        "last_name": last_name.strip(),
        "password":password,
        "birth_date": birth_date.isoformat() if birth_date else None,
        "channel": channel,
    }
    issued = issue_otp(
        purpose=PURPOSE_SIGNUP,
        channel=channel,
        identifier=identifier,
        extra=extra,
    )
    _queue_otp(
        channel=channel,
        identifier=identifier,
        delivery_key=issued["delivery_key"],
        purpose=PURPOSE_SIGNUP,
    )
    return {
        "channel": channel,
        "identifier": identifier,
        "expires_in": issued["expires_in"],
    }


def verify_registration(*, channel: str, identifier: str, otp: str) -> dict[str, Any]:
    """Consume a signup OTP, create the user, and issue authentication tokens."""

    channel = channel.strip().lower()
    identifier = normalize_identifier(channel=channel, identifier=identifier)
    record = verify_otp(purpose=PURPOSE_SIGNUP, channel=channel, identifier=identifier, otp=otp)
    payload = record.get("extra") or {}

    with transaction.atomic():
        if user_get_by_phone(phone=payload["phone"]):
            raise AlreadyExistsError(_("An account with this phone number already exists."))
        email = payload.get("email") or ""
        if email and user_get_by_email(email=email):
            raise AlreadyExistsError(_("An account with this email already exists."))

        birth_raw = payload.get("birth_date")
        birth_date = date.fromisoformat(birth_raw) if birth_raw else None
        data = {
            "phone" : payload["phone"],
            "username": payload["username"],
            "last_name": payload["last_name"],
            "email": email,
            "birth_date" : birth_date,
            "is_active" : True,
            "is_staff" : False,
            "is_superuser" : False,
            "is_vip" : False,
            "is_phone_verified" : channel == "phone",
            "is_email_verified": channel == "email",
            "password" : payload["password"]
        }
        user = create_user(
            data=data
        )

    logger.info("User registered id=%s channel=%s", user.pk, channel)
    return _auth_payload(user)


def login_with_password(*, channel: str, identifier: str, password: str) -> dict[str, Any]:
    """
    Authenticate with Django's password hasher.

    Missing users, wrong passwords, inactive accounts, and unverified
    identifiers all raise the same error to prevent account enumeration.
    """

    channel = channel.strip().lower()
    try:
        identifier = normalize_identifier(channel=channel, identifier=identifier)
    except Exception:
        raise _GENERIC_LOGIN_ERROR() from None

    user = user_get_for_login(channel=channel, identifier=identifier)
    print("_______________________________", user)
    if user is None or not user.is_active:
        raise _GENERIC_LOGIN_ERROR()

    if channel == "phone" and not user.is_phone_verified:
        raise _GENERIC_LOGIN_ERROR()
    if channel == "email" and not user.is_email_verified:
        raise _GENERIC_LOGIN_ERROR()

    authenticated = authenticate(username=user.phone, password=password)
    if authenticated is None:
        raise _GENERIC_LOGIN_ERROR()

    return _auth_payload(authenticated)


def request_password_reset(*, channel: str, identifier: str) -> dict[str, str]:
    """Send a reset OTP only to a verified, registered identifier. Always generic."""

    channel = channel.strip().lower()
    generic = {"message": str(_GENERIC_RESET_MESSAGE)}
    try:
        identifier = normalize_identifier(channel=channel, identifier=identifier)
    except Exception:
        return generic

    user = user_get_for_login(channel=channel, identifier=identifier)
    verified = False
    if user is not None and user.is_active:
        if channel == "phone":
            verified = user.is_phone_verified
        elif channel == "email":
            verified = user.is_email_verified and bool(user.email)

    if not verified:
        return generic

    try:
        issued = issue_otp(
            purpose=PURPOSE_PASSWORD_RESET,
            channel=channel,
            identifier=identifier,
            extra={"user_id": user.pk},
        )
        _queue_otp(
            channel=channel,
            identifier=identifier,
            delivery_key=issued["delivery_key"],
            purpose=PURPOSE_PASSWORD_RESET,
        )
    except Exception:
        logger.warning("Password reset OTP could not be issued")
    return generic


def confirm_password_reset(
    *,
    channel: str,
    identifier: str,
    otp: str,
    new_password: str,
) -> dict[str, str]:
    """Validate the reset OTP, set a new password, and revoke refresh tokens."""

    channel = channel.strip().lower()
    identifier = normalize_identifier(channel=channel, identifier=identifier)
    record = verify_otp(
        purpose=PURPOSE_PASSWORD_RESET,
        channel=channel,
        identifier=identifier,
        otp=otp,
    )
    user_id = (record.get("extra") or {}).get("user_id")
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user is None:
        raise InvalidCredentialsError()

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ValidationFailedError(
            _("Validation error."),
            extra={"password": list(exc.messages)},
        ) from exc

    with transaction.atomic():
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        blacklist_user_refresh_tokens(user)

    logger.info("Password reset completed user_id=%s", user.pk)
    return {"message": str(_("Password has been reset."))}


def _placeholder_phone_for_google(sub: str) -> str:
    digest = hashlib.sha256(sub.encode()).hexdigest()
    return f"g{digest[:19]}"


def authenticate_with_google(*, id_token: str) -> dict[str, Any]:
    """
    Verify a Google ID token and issue project tokens.

    Linking happens only when the Google email is verified and already belongs
    to an account that has a verified email and no different Google subject.
    """

    claims = _verify_google_id_token(id_token)
    sub = str(claims.get("sub") or "")
    if not sub:
        raise UnauthorizedError(_("Invalid Google token."))

    email_verified = bool(claims.get("email_verified"))
    email = ""
    if email_verified and claims.get("email"):
        try:
            email = normalize_email(str(claims["email"]))
        except Exception:
            email = ""

    existing = user_get_by_google_sub(google_sub=sub)
    if existing is not None:
        if not existing.is_active:
            raise InvalidCredentialsError()
        return _auth_payload(existing)

    if email:
        by_email = user_get_by_email(email=email)
        if by_email is not None:
            if by_email.google_sub and by_email.google_sub != sub:
                raise AlreadyExistsError(_("This email is already linked to another account."))
            if not by_email.is_email_verified:
                raise AlreadyExistsError(_("This email is already linked to another account."))
            with transaction.atomic():
                by_email.google_sub = sub
                by_email.is_email_verified = True
                by_email.save(update_fields=["google_sub", "is_email_verified", "updated_at"])
            return _auth_payload(by_email)

    given = str(claims.get("given_name") or claims.get("name") or "Google")
    family = str(claims.get("family_name") or "User")
    phone = _placeholder_phone_for_google(sub)

    with transaction.atomic():
        user = User.objects.create_user(
            phone=phone,
            password=None,
            username=given[:150],
            last_name=family[:150],
            email=email,
            is_active=True,
            is_phone_verified=False,
            is_email_verified=bool(email),
            google_sub=sub,
        )
        user.set_unusable_password()
        user.save(update_fields=["password", "updated_at"])

    logger.info("Google user created id=%s", user.pk)
    return _auth_payload(user)


def _verify_google_id_token(raw_token: str) -> dict[str, Any]:
    """Validate signature, audience, issuer, and expiry through google-auth."""

    from django.conf import settings

    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "") or ""
    if not client_id:
        raise UnauthorizedError(_("Google sign-in is not configured."))

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError as exc:
        raise UnauthorizedError(_("Google sign-in is not available.")) from exc

    try:
        claims = google_id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            audience=client_id,
        )
    except Exception as exc:
        raise UnauthorizedError(_("Invalid Google token.")) from exc

    issuer = claims.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise UnauthorizedError(_("Invalid Google token."))
    return claims
