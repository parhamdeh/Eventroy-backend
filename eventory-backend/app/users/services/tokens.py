"""Issue and revoke SimpleJWT tokens for the custom User model."""

from __future__ import annotations

from typing import Any

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from app.core.exceptions import TokenInvalidError


def issue_tokens_for_user(user: Any) -> dict[str, str]:
    """Return access and refresh token strings for `user`."""

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def rotate_refresh_token(refresh_token: str) -> dict[str, str]:
    """Validate a refresh token and issue a new access token (and rotated refresh)."""

    serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
    try:
        serializer.is_valid(raise_exception=True)
    except (TokenError, Exception) as exc:
        raise TokenInvalidError() from exc
    data = serializer.validated_data
    return {
        "access": str(data["access"]),
        "refresh": str(data.get("refresh", refresh_token)),
    }


def blacklist_user_refresh_tokens(user: Any) -> None:
    """Blacklist all outstanding refresh tokens for `user` after a password reset."""

    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
    except ImportError:
        return

    for outstanding in OutstandingToken.objects.filter(user=user).iterator():
        BlacklistedToken.objects.get_or_create(token=outstanding)
