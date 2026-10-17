"""Normalize and validate phone numbers and email addresses."""

from __future__ import annotations

import re

import phonenumbers
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

_DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_CHANNEL_PHONE = "phone"
_CHANNEL_EMAIL = "email"


def normalize_phone(value: str) -> str:
    """Return an E.164 phone number, defaulting to Iran when no country code is given."""

    if not value or not str(value).strip():
        raise ValidationError(_("A phone number is required."), code="required")

    raw = str(value).strip().translate(_DIGIT_TRANSLATION)
    raw = re.sub(r"[\s\-()]", "", raw)
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    elif raw.startswith("0"):
        raw = "+98" + raw[1:]
    elif raw.startswith("9") and len(raw) == 10:
        raw = "+98" + raw
    elif raw.startswith("98") and not raw.startswith("+"):
        raw = "+" + raw
    elif not raw.startswith("+"):
        raw = "+" + raw

    try:
        parsed = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException as exc:
        raise ValidationError(_("Enter a valid phone number."), code="invalid") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError(_("Enter a valid phone number."), code="invalid")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def normalize_email(value: str) -> str:
    """Return a lowercase, stripped email address."""

    if not value or not str(value).strip():
        raise ValidationError(_("An email address is required."), code="required")

    email = str(value).strip().lower()
    try:
        validate_email(email)
    except ValidationError as exc:
        raise ValidationError(_("Enter a valid email address."), code="invalid") from exc
    return email


def normalize_identifier(*, channel: str, identifier: str) -> str:
    """Normalize `identifier` according to `channel` (`phone` or `email`)."""

    if channel == _CHANNEL_PHONE:
        return normalize_phone(identifier)
    if channel == _CHANNEL_EMAIL:
        return normalize_email(identifier)
    raise ValidationError(_("Unsupported verification channel."), code="invalid")
