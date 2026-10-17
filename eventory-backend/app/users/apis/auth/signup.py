"""Sign-up and OTP verification endpoints."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.api.throttle import OTPRequestThrottle
from app.users.apis.auth.serializers import (
    AuthTokenResponseSerializer,
    OTPVerifySerializer,
    PendingOtpResponseSerializer,
    SignUpSerializer,
    UserPublicSerializer,
)
from app.users.services.auth import register_user, verify_registration


class SignUpApi(APIView):
    """Create a pending registration and send a verification OTP."""

    permission_classes = (AllowAny,)
    throttle_classes = (OTPRequestThrottle,)

    @extend_schema(
        tags=["auth"],
        request=SignUpSerializer,
        responses={202: PendingOtpResponseSerializer},
        auth=[],
        description=(
            "Validate registration data, store a pending profile in cache, and "
            "queue an OTP on the selected channel. The user row is created only "
            "after OTP verification."
        ),
    )
    def post(self, request: Request) -> Response:
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = register_user(**serializer.validated_data)
        return Response(data, status=status.HTTP_202_ACCEPTED)


class VerifyRegistrationApi(APIView):
    """Verify a signup OTP and return authentication tokens."""

    permission_classes = (AllowAny,)
    throttle_classes = (OTPRequestThrottle,)

    @extend_schema(
        tags=["auth"],
        request=OTPVerifySerializer,
        responses={200: AuthTokenResponseSerializer},
        auth=[],
        description="Consume a single-use signup OTP and issue access/refresh tokens.",
    )
    def post(self, request: Request) -> Response:
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = verify_registration(**serializer.validated_data)
        payload = {
            "access": result["access"],
            "refresh": result["refresh"],
            "user": UserPublicSerializer(result["user"]).data,
        }
        return Response(payload, status=status.HTTP_200_OK)
