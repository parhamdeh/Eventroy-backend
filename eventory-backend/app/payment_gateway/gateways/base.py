from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GatewayRequestResult:
    authority: str
    payment_url: str


@dataclass(frozen=True, slots=True)
class GatewayVerifyResult:
    ref_id: str
    card_pan: str = ""
    fee: int = 0


class BaseGateway(ABC):
    """
    Contract every gateway implements.

    Implementations must raise:
      * GatewayRejected    - gateway answered and said no (definitive),
      * GatewayUnavailable - could not get a trustworthy answer (unknown outcome).
    """

    name: str

    @abstractmethod
    def request(
        self,
        *,
        amount: int,
        description: str,
        callback_url: str,
        mobile: str | None = None,
    ) -> GatewayRequestResult: ...

    @abstractmethod
    def verify(self, *, authority: str, amount: int) -> GatewayVerifyResult: ...