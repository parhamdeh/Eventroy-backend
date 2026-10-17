"""Refresh-token rotation using SimpleJWT."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.api.throttle import AuthRateThrottle
from app.users.apis.auth.serializers import TokenRefreshRequestSerializer
from app.users.services.tokens import rotate_refresh_token


class TokenRefreshApi(APIView):
    """Issue a new access token (and rotated refresh token) from a valid refresh token."""

    permission_classes = (AllowAny,)
    throttle_classes = (AuthRateThrottle,)

    @extend_schema(
        tags=["auth"],
        request=TokenRefreshRequestSerializer,
        responses={200: TokenRefreshRequestSerializer},
        auth=[],
        description="Rejects expired, invalid, and blacklisted refresh tokens.",
    )
    def post(self, request: Request) -> Response:
        serializer = TokenRefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = rotate_refresh_token(serializer.validated_data["refresh"])
        return Response(tokens, status=status.HTTP_200_OK)
