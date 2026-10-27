import logging
import re

import requests
from django.conf import settings

from app.payment_gateway.exception import GatewayRejected, GatewayUnavailable
from app.payment_gateway.gateways.base import (
    BaseGateway,
    GatewayRequestResult,
    GatewayVerifyResult,
)

logger = logging.getLogger(__name__)

_HEADERS = {"accept": "application/json", "content-type": "application/json"}
_MOBILE_RE = re.compile(r"^09\d{9}$")


def _normalize_mobile(raw) -> str | None:
    """Zarinpal rejects badly formatted mobiles, so send 09xxxxxxxxx or nothing."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "0" + digits
    return digits if _MOBILE_RE.match(digits) else None


class ZarinpalGateway(BaseGateway):
    name = "zarinpal"

    def _post(self, url: str, payload: dict) -> tuple[dict, dict]:
        """POST and return (data, errors) as dicts. Never returns lists/None."""
        try:
            response = requests.post(
                url,
                json=payload,
                headers=_HEADERS,
                timeout=settings.ZARINPAL_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("Zarinpal unreachable: %s", exc)
            raise GatewayUnavailable("Payment gateway is unreachable.") from exc

        if response.status_code >= 500:
            logger.warning("Zarinpal 5xx: %s", response.status_code)
            raise GatewayUnavailable("Payment gateway is unavailable.")

        try:
            body = response.json()
        except ValueError as exc:
            raise GatewayUnavailable("Invalid response from gateway.") from exc

        if not isinstance(body, dict):
            raise GatewayUnavailable("Invalid response from gateway.")

        # On failure Zarinpal sends `"data": []` (a list!) and `errors` as a dict.
        data = body.get("data")
        errors = body.get("errors")
        return (
            data if isinstance(data, dict) else {},
            errors if isinstance(errors, dict) else {},
        )

    def request(self, *, amount, description, callback_url, mobile=None):
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": amount,
            # Our amounts are tomans. Without this Zarinpal assumes rials
            # and the user would be charged 10x less. Confirm in sandbox.
            "currency": "IRT",
            "description": description,
            "callback_url": callback_url,
        }
        mobile = _normalize_mobile(mobile)
        if mobile:
            payload["metadata"] = {"mobile": mobile}

        data, errors = self._post(settings.ZARINPAL_REQUEST_URL, payload)

        if data.get("code") != 100 or not data.get("authority"):
            code = errors.get("code") or data.get("code")
            logger.error("Zarinpal request rejected: code=%s errors=%s", code, errors)
            raise GatewayRejected("Gateway refused the payment request.", code=code)

        authority = data["authority"]
        return GatewayRequestResult(
            authority=authority,
            payment_url=f"{settings.ZARINPAL_STARTPAY_URL}{authority}",
        )

    def verify(self, *, authority, amount):
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "authority": authority,
            "amount": amount,
        }
        data, errors = self._post(settings.ZARINPAL_VERIFY_URL, payload)

        # 100 = verified now, 101 = already verified (replay / retry).
        if data.get("code") not in (100, 101) or not data.get("ref_id"):
            code = errors.get("code") or data.get("code")
            logger.warning("Zarinpal verify rejected: code=%s errors=%s", code, errors)
            raise GatewayRejected("Gateway could not verify the payment.", code=code)

        return GatewayVerifyResult(
            ref_id=str(data["ref_id"]),
            card_pan=str(data.get("card_pan") or ""),
            fee=int(data.get("fee") or 0),
        )