
from app.core.exceptions import ApplicationError


class GatewayError(ApplicationError):
    """
    Represent an error raised during payment gateway communication.

    This exception is used for gateway failures such as network errors,
    invalid responses, and unsuccessful payment verification.
    """

    default_code = "payment_gateway_error"
    default_message = "Payment gateway request failed."
