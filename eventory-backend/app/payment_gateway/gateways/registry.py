from django.core.exceptions import ImproperlyConfigured

from app.payment_gateway.gateways.base import BaseGateway
from app.payment_gateway.gateways.zarinpal import ZarinpalGateway

_GATEWAYS: dict[str, type[BaseGateway]] = {
    ZarinpalGateway.name: ZarinpalGateway,
}


def get_gateway(name: str) -> BaseGateway:
    try:
        return _GATEWAYS[name]()
    except KeyError:
        raise ImproperlyConfigured(f"Unknown payment gateway: {name!r}") from None