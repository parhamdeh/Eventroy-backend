
from app.payment_gateway.gateways.zarinpal import ZarinPalGateway


class GatewayFactory:
    """Create payment gateway instances based on the gateway name."""

    _gateways = {
        "zarinpal": ZarinPalGateway,
    }

    @classmethod
    def get(cls, name: str) -> ZarinPalGateway:
        """
        Return an instance of the requested payment gateway.

        Args:
            name: The gateway identifier.

        Returns:
            An instance of the selected payment gateway.

        Raises:
            ValueError: If the gateway is not supported.
        """
        gateway_class = cls._gateways.get(name.lower())

        if gateway_class is None:
            raise ValueError(f"Unsupported payment gateway: {name}")

        return gateway_class()
