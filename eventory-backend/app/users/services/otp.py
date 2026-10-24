"""Cryptographically secure, cache-backed OTP lifecycle."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from app.core.exceptions import (
    BadRequestError,
    GoneError,
    ServiceUnavailableError,
    TooManyRequestsError,
)

logger = logging.getLogger(__name__)

PURPOSE_SIGNUP = "signup"
PURPOSE_PASSWORD_RESET = "password_reset"


def generate_otp(length: int | None = None) -> str:
    """Return a cryptographically secure numeric OTP of `length` digits."""

    digits = length or int(getattr(settings, "OTP_LENGTH", 6))
    return f"{secrets.randbelow(10**digits):0{digits}d}"


def _prefix() -> str:
    return str(getattr(settings, "OTP_CACHE_PREFIX", "eventory:otp"))


def verify_key(*, purpose: str, channel: str, identifier: str) -> str:
    """Cache key holding the hashed OTP and metadata."""

    return f"{_prefix()}:{purpose}:{channel}:{identifier}"


def _cooldown_key(*, purpose: str, channel: str, identifier: str) -> str:
    return f"{_prefix()}:cooldown:{purpose}:{channel}:{identifier}"


def _lock_key(verify_cache_key: str) -> str:
    return f"{verify_cache_key}:lock"


def _delivery_key(*, purpose: str, channel: str, identifier: str) -> str:
    return f"{_prefix()}:send:{purpose}:{channel}:{identifier}"


def _digest(otp: str) -> str:
    secret = str(getattr(settings, "SECRET_KEY", "")).encode()
    return hmac.new(secret, otp.encode(), hashlib.sha256).hexdigest()


def issue_otp(
    *,
    purpose: str,
    channel: str,
    identifier: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Store a hashed OTP and a short-lived plaintext delivery payload.

    Enforces a resend cooldown. Does not log or return the OTP.
    """

    ttl = int(getattr(settings, "OTP_TTL_SECONDS", 120))
    cooldown = int(getattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 60))
    delivery_ttl = int(getattr(settings, "OTP_DELIVERY_TTL_SECONDS", 60))

    cooldown_key = _cooldown_key(purpose=purpose, channel=channel, identifier=identifier)
    try:
        if not cache.add(cooldown_key, 1, timeout=cooldown):
            raise TooManyRequestsError(_("Please wait before requesting another code."))
    except TooManyRequestsError:
        raise
    except Exception as exc:
        logger.warning("OTP cache unavailable while issuing a code")
        raise ServiceUnavailableError(_("Verification service is temporarily unavailable.")) from exc

    otp = generate_otp()
    record: dict[str, Any] = {
        "digest": _digest(otp),
        "attempts": 0,
        "purpose": purpose,
        "channel": channel,
        "identifier": identifier,
        "extra": extra or {},
    }
    key = verify_key(purpose=purpose, channel=channel, identifier=identifier)
    delivery = _delivery_key(purpose=purpose, channel=channel, identifier=identifier)

    try:
        cache.set(key, record, timeout=ttl)
        cache.set(delivery, otp, timeout=delivery_ttl)
        stored_record = cache.get(key)
        stored_delivery = cache.get(delivery)

        if stored_record is None or stored_delivery is None:
            raise RuntimeError("OTP cache write verification failed.")
    except Exception as exc:
        cache.delete(cooldown_key)
        logger.warning("OTP cache unavailable while storing a code")
        raise ServiceUnavailableError(_("Verification service is temporarily unavailable.")) from exc

    logger.info("OTP issued purpose=%s channel=%s", purpose, channel)
    return {
        "expires_in": ttl,
        "delivery_key": delivery,
        "verify_key": key,
    }


def verify_otp(
    *,
    purpose: str,
    channel: str,
    identifier: str,
    otp: str,
) -> dict[str, Any]:
    """
    Consume a valid OTP exactly once.

    Concurrent callers contend on an exclusive lock. Wrong attempts increment
    a counter; exceeding OTP_MAX_ATTEMPTS deletes the record.
    """

    key = verify_key(purpose=purpose, channel=channel, identifier=identifier)
    lock = _lock_key(key)
    try:
        acquired = cache.add(lock, 1, timeout=5)
    except Exception as exc:
        logger.warning("OTP cache unavailable while verifying a code")
        raise ServiceUnavailableError(_("Verification service is temporarily unavailable.")) from exc

    if not acquired:
        raise TooManyRequestsError(_("Verification is already in progress. Try again."))

    try:
        record = cache.get(key)
        if not record:
            raise GoneError(_("Verification code expired."), code="otp_expired")

        attempts = int(record.get("attempts", 0))
        max_attempts = int(getattr(settings, "OTP_MAX_ATTEMPTS", 5))
        if attempts >= max_attempts:
            cache.delete(key)
            raise TooManyRequestsError(_("Too many invalid verification attempts."))

        submitted = (otp or "").strip()
        if len(submitted) != int(getattr(settings, "OTP_LENGTH", 6)) or not hmac.compare_digest(
            record.get("digest", ""),
            _digest(submitted),
        ):
            record["attempts"] = attempts + 1
            ttl = int(getattr(settings, "OTP_TTL_SECONDS", 120))
            if record["attempts"] >= max_attempts:
                cache.delete(key)
                raise TooManyRequestsError(_("Too many invalid verification attempts."))
            cache.set(key, record, timeout=ttl)
            raise BadRequestError(_("Invalid verification code."), code="otp_invalid")

        cache.delete(key)
        cache.delete(_delivery_key(purpose=purpose, channel=channel, identifier=identifier))
        logger.info("OTP consumed purpose=%s channel=%s", purpose, channel)
        return record
    finally:
        cache.delete(lock)
