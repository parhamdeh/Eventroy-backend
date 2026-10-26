
from typing import Any

import requests
from django.conf import settings

from app.core.exceptions import ApplicationError
from app.payment_gateway.exception import GatewayError
from app.payment_gateway.interface import BaseGateway


class ZarinPalGateway(BaseGateway):
    """
    Communicate with the ZarinPal payment API.

    Internal payment amounts must use the application's agreed
    monetary unit. Conversion to the gateway's required unit belongs
    at this integration boundary.
    """

    def __init__(self) -> None:
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.request_url = settings.ZARINPAL_REQUEST_URL
        self.verify_url = settings.ZARINPAL_VERIFY_URL
        self.start_pay_url = settings.ZARINPAL_START_PAY_URL
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.timeout = (3.05, 10)

    @staticmethod
    def _post_json(
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a JSON request and validate the response format."""
        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=(3.05, 10),
            )
            response.raise_for_status()
            result = response.json()

        except requests.Timeout as exc:
            raise GatewayError(
                "Payment gateway timed out."
            ) from exc

        except requests.RequestException as exc:
            raise GatewayError(
                "Could not communicate with the payment gateway."
            ) from exc

        except ValueError as exc:
            raise GatewayError(
                "Payment gateway returned an invalid response."
            ) from exc

        if not isinstance(result, dict):
            raise GatewayError(
                "Payment gateway returned an unexpected response."
            )

        return result

    @staticmethod
    def _validate_amount(amount: Any) -> int:
        """Require a positive integer amount."""
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise ApplicationError("Amount must be an integer.")

        if amount <= 0:
            raise ApplicationError("Amount must be greater than zero.")

        return amount

    def request(self, payment: dict[str, Any]) -> dict[str, str]:
        """Create a payment request with ZarinPal."""
        amount = self._validate_amount(payment.get("amount"))

        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "description": payment.get("description", "Wallet charge"),
            "callback_url": self.callback_url,
            "metadata": {
                "mobile": str(payment.get("phone") or ""),
            },
        }

        result = self._post_json(self.request_url, payload)
        data = result.get("data")

        if not isinstance(data, dict):
            raise GatewayError("Invalid payment request response.")

        if data.get("code") != 100:
            raise GatewayError(
                result.get("errors") or data
            )

        authority = data.get("authority")

        if not isinstance(authority, str) or not authority:
            raise GatewayError(
                "Payment gateway did not return an authority."
            )

        return {
            "authority": authority,
            "payment_url": f"{self.start_pay_url}{authority}",
        }

    def verify(self, payment: Any) -> dict[str, str]:
        """Verify a payment with ZarinPal."""
        amount = self._validate_amount(int(payment.amount))

        if not payment.authority:
            raise ApplicationError(
                "Payment has no gateway authority."
            )

        payload = {
            "merchant_id": self.merchant_id,
            "authority": payment.authority,
            "amount": amount,
        }

        result = self._post_json(self.verify_url, payload)
        data = result.get("data")

        if not isinstance(data, dict):
            raise GatewayError("Invalid payment verification response.")

        code = data.get("code")

        if code not in (100, 101):
            raise GatewayError(
                result.get("errors")
                or data.get("message")
                or "Payment verification failed."
            )

        ref_id = data.get("ref_id")

        if ref_id is None:
            raise GatewayError(
                "Payment verification returned no reference ID."
            )

        return {"ref_id": str(ref_id)}
