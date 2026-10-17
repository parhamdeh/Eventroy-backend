"""Read-side queries for the User model."""

from __future__ import annotations

from django.db.models import QuerySet

from app.users.models import User


def user_get_by_id(*, user_id: int) -> User | None:
    """Return a user by primary key, or None."""

    return User.objects.filter(pk=user_id).first()


def user_get_by_phone(*, phone: str) -> User | None:
    """Return a user with the exact normalized phone, or None."""

    return User.objects.filter(phone=phone).first()


def user_get_by_email(*, email: str) -> User | None:
    """Return a user with the exact lowercase email, or None."""

    if not email:
        return None
    return User.objects.filter(email=email).first()


def user_get_by_google_sub(*, google_sub: str) -> User | None:
    """Return the user linked to a Google `sub` claim, or None."""

    if not google_sub:
        return None
    return User.objects.filter(google_sub=google_sub).first()


def user_get_for_login(*, channel: str, identifier: str) -> User | None:
    """Resolve a user by login channel without leaking existence to callers."""

    if channel == "phone":
        return user_get_by_phone(phone=identifier)
    if channel == "email":
        return user_get_by_email(email=identifier)
    return None


def user_list(
    *,
    user_id: int | None = None,
    phone: str | None = None,
    email: str | None = None,
    is_vip: bool | None = None,
) -> QuerySet[User]:
    """
    Build an admin listing queryset.

    Filters are AND-combined and evaluated in the database. Password hashes
    are deferred so they are never loaded for list views.
    """

    queryset = User.objects.all().defer("password")
    if user_id is not None:
        queryset = queryset.filter(pk=user_id)
    if phone:
        queryset = queryset.filter(phone=phone)
    if email:
        queryset = queryset.filter(email=email)
    if is_vip is not None:
        queryset = queryset.filter(is_vip=is_vip)
    return queryset
