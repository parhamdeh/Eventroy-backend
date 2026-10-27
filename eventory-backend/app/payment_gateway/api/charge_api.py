import logging
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.payment_gateway.enums import PaymentStatus
from app.payment_gateway.exception import GatewayUnavailable, PaymentNotFound
from app.payment_gateway.throttle import PaymentCallbackThrottle, PaymentCreateThrottle
from app.payment_gateway.api.serializers import (
    VerifyQuerySerializer,
    WalletChargeInputSerializer,
    WalletChargeOutputSerializer,
)
from app.payment_gateway.services import initiate_wallet_charge, verify_payment

logger = logging.getLogger(__name__)

_RESULT_BY_STATUS = {
    PaymentStatus.SUCCESS: "success",
    PaymentStatus.CANCELED: "canceled",
    PaymentStatus.FAILED: "failed",
    PaymentStatus.EXPIRED: "failed",
    PaymentStatus.PENDING: "pending",
}


class WalletChargeCreateAPI(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentCreateThrottle]

    @extend_schema(
        tags=["Payment"],
        summary="Start a wallet charge",
        request=WalletChargeInputSerializer,
        responses={
            201: WalletChargeOutputSerializer,
            400: OpenApiResponse(description="Invalid amount."),
            401: OpenApiResponse(description="Not authenticated."),
            502: OpenApiResponse(description="Payment gateway error."),
        },
    )
    def post(self, request):
        serializer = WalletChargeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        initiated = initiate_wallet_charge(
            user=request.user,
            amount=serializer.validated_data["amount"],
        )
        return Response(
            WalletChargeOutputSerializer(initiated).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentVerifyAPI(APIView):
    """
    Gateway callback. The user's *browser* lands here (GET, no JWT), so we
    answer with a redirect to the frontend result page, not JSON.

    Security does not depend on who calls this: we only trust the
    server-to-server verify against the amount stored in our DB.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [PaymentCallbackThrottle]

    @extend_schema(
        tags=["Payment"],
        summary="Zarinpal callback (browser redirect)",
        parameters=[VerifyQuerySerializer],
        responses={302: OpenApiResponse(description="Redirect to frontend result page.")},
    )
    def get(self, request):
        query = VerifyQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return self._redirect("failed")

        try:
            payment = verify_payment(
                authority=query.validated_data["Authority"],
                callback_status=query.validated_data["Status"],
            )
        except PaymentNotFound:
            return self._redirect("failed")
        except GatewayUnavailable:
            # Outcome unknown; payment is still PENDING and safe to retry.
            return self._redirect("pending")

        return self._redirect(_RESULT_BY_STATUS[payment.status], payment.pk)

    @staticmethod
    def _redirect(result: str, payment_id: int | None = None):
        params = {"status": result}
        if payment_id is not None:
            params["payment_id"] = payment_id
        # Fixed base URL from settings => no open-redirect.
        return redirect(f"{settings.PAYMENT_RESULT_REDIRECT_URL}?{urlencode(params)}")