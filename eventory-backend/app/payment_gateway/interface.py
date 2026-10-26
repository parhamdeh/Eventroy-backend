
from abc import ABC, abstractmethod
from typing import Any


class BaseGateway(ABC):
    """Define the contract for payment gateway integrations."""

    @abstractmethod
    def request(self, payment: dict[str, Any]) -> dict[str, str]:
        """Create a payment request and return its redirect details."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, payment: Any) -> dict[str, str]:
        """Verify a payment and return its gateway reference."""
        raise NotImplementedError
