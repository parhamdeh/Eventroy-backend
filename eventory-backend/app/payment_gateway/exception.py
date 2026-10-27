# Adjust the import path to wherever your ApplicationError lives.
from app.core.exceptions import ApplicationError


class PaymentError(ApplicationError):
    """Base class for payment errors."""


class PaymentNotFound(PaymentError):
    """No payment matches the given authority."""


class GatewayError(PaymentError):
    """Base class for errors coming from a payment gateway."""

    def __init__(self, message: str = "Payment gateway error.", *, code=None):
        super().__init__(message)
        self.code = code


class GatewayUnavailable(GatewayError):
    """Network failure / timeout / 5xx. Outcome is UNKNOWN: do not fail the payment."""


class GatewayRejected(GatewayError):
    """The gateway answered and definitively said no."""