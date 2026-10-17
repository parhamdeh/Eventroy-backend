"""Administrator workflows for staff creation and VIP updates."""

from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from app.core.exceptions import AlreadyExistsError, NotFoundError, ValidationFailedError
from app.users.identifiers import normalize_email, normalize_phone
from app.users.models import User
from app.users.selectors.users import user_get_by_email, user_get_by_id, user_get_by_phone


def create_staff_admin(
    *,
    phone: str,
    password: str,
    username: str,
    last_name: str,
    email: str = "",
) -> User:
    """
    Create a staff administrator.

    Superuser privileges are never granted here. VIP is always false.
    """

    phone = normalize_phone(phone)
    email = normalize_email(email) if email else ""
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

    with transaction.atomic():
        user = User.objects.create_user(
            phone=phone,
            password=password,
            username=username.strip(),
            last_name=last_name.strip(),
            email=email,
            is_active=True,
            is_staff=True,
            is_superuser=False,
            is_vip=False,
            is_phone_verified=True,
            is_email_verified=bool(email),
        )
    return user


def set_user_vip(*, user_id: int, is_vip: bool) -> User:
    """Set VIP status for an existing user."""

    user = user_get_by_id(user_id=user_id)
    if user is None:
        raise NotFoundError(_("User not found."))

    if user.is_vip == is_vip:
        return user

    with transaction.atomic():
        user.is_vip = is_vip
        user.save(update_fields=["is_vip", "updated_at"])
    return user
