"""Password login, password reset, and Google OAuth endpoints."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.api.throttle import AuthRateThrottle, OTPRequestThrottle
from app.users.apis.auth.serializers import (
    AuthTokenResponseSerializer,
    GoogleAuthSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserPublicSerializer,
)
from app.users.services.auth import (
    authenticate_with_google,
    confirm_password_reset,
    login_with_password,
    request_password_reset,
)


class LoginApi(APIView):
    """Password authentication with phone or email."""

    permission_classes = (AllowAny,)
    throttle_classes = (AuthRateThrottle,)

    @extend_schema(
        tags=["auth"],
        request=LoginSerializer,
        responses={200: AuthTokenResponseSerializer},
        auth=[],
        description="Authenticate with Django's password hasher. Failures share one error.",
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = login_with_password(**serializer.validated_data)
        payload = {
            "access": result["access"],
            "refresh": result["refresh"],
            "user": UserPublicSerializer(result["user"]).data,
        }
        return Response(payload, status=status.HTTP_200_OK)


class PasswordResetRequestApi(APIView):
    """Request a password-reset OTP. Always returns a generic success payload."""

    permission_classes = (AllowAny,)
    throttle_classes = (OTPRequestThrottle,)

    @extend_schema(
        tags=["auth"],
        request=PasswordResetRequestSerializer,
        responses={200: PasswordResetRequestSerializer},
        auth=[],
        description="Sends a reset OTP only to a verified registered identifier.",
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = request_password_reset(**serializer.validated_data)
        return Response(data, status=status.HTTP_200_OK)


class PasswordResetConfirmApi(APIView):
    """Confirm a password-reset OTP and set a new password."""

    permission_classes = (AllowAny,)
    throttle_classes = (OTPRequestThrottle,)

    @extend_schema(
        tags=["auth"],
        request=PasswordResetConfirmSerializer,
        responses={200: PasswordResetRequestSerializer},
        auth=[],
        description="Single-use OTP. Outstanding refresh tokens are blacklisted.",
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = confirm_password_reset(**serializer.validated_data)
        return Response(data, status=status.HTTP_200_OK)


class GoogleAuthApi(APIView):
    """Exchange a Google ID token for project access and refresh tokens."""

    permission_classes = (AllowAny,)
    throttle_classes = (AuthRateThrottle,)

    @extend_schema(
        tags=["auth"],
        request=GoogleAuthSerializer,
        responses={200: AuthTokenResponseSerializer},
        auth=[],
        description=(
            "The frontend obtains a Google ID token (GIS). This API verifies "
            "iss/aud/exp/signature with google-auth and uses Google `sub` as identity."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = authenticate_with_google(id_token=serializer.validated_data["id_token"])
        payload = {
            "access": result["access"],
            "refresh": result["refresh"],
            "user": UserPublicSerializer(result["user"]).data,
        }
        return Response(payload, status=status.HTTP_200_OK)
