"""
Needs a `user` fixture from your conftest (and pytest-django).
Gateway is faked, so no network is touched.
"""
import pytest

from app.payment_gateway import services
from app.payment_gateway.enums import PaymentStatus
from app.payment_gateway.exception import GatewayRejected, GatewayUnavailable
from app.payment_gateway.gateways.base import GatewayRequestResult, GatewayVerifyResult
from app.payment_gateway.models import Payment
from app.users.models import Wallet, WalletTransaction

pytestmark = pytest.mark.django_db


class FakeGateway:
    name = "zarinpal"

    def __init__(self, *, verify_exc=None, request_exc=None):
        self.verify_exc = verify_exc
        self.request_exc = request_exc
        self.verify_calls = 0

    def request(self, **kwargs):
        if self.request_exc:
            raise self.request_exc
        return GatewayRequestResult(authority="A123", payment_url="https://pay/A123")

    def verify(self, **kwargs):
        self.verify_calls += 1
        if self.verify_exc:
            raise self.verify_exc
        return GatewayVerifyResult(ref_id="REF1", card_pan="6037****1234", fee=100)


@pytest.fixture
def use_gateway(monkeypatch):
    def _use(gateway):
        monkeypatch.setattr(services, "get_gateway", lambda name: gateway)
        return gateway
    return _use


def _initiate(user):
    return services.initiate_wallet_charge(user=user, amount=50_000)


def _balance(user):
    return Wallet.objects.get(user=user).balance


def test_successful_charge_credits_wallet_once(user, use_gateway):
    use_gateway(FakeGateway())
    _initiate(user)

    p1 = services.verify_payment(authority="A123", callback_status="OK")
    p2 = services.verify_payment(authority="A123", callback_status="OK")  # replay

    assert p1.status == p2.status == PaymentStatus.SUCCESS
    assert _balance(user) == 50_000
    assert WalletTransaction.objects.count() == 1


def test_gateway_called_only_once_on_replay(user, use_gateway):
    gw = use_gateway(FakeGateway())
    _initiate(user)
    services.verify_payment(authority="A123", callback_status="OK")
    services.verify_payment(authority="A123", callback_status="OK")
    assert gw.verify_calls == 1


def test_nok_cancels_without_credit(user, use_gateway):
    gw = use_gateway(FakeGateway())
    _initiate(user)

    payment = services.verify_payment(authority="A123", callback_status="NOK")

    assert payment.status == PaymentStatus.CANCELED
    assert gw.verify_calls == 0
    assert not Wallet.objects.filter(user=user, balance__gt=0).exists()


def test_rejected_verify_marks_failed(user, use_gateway):
    use_gateway(FakeGateway(verify_exc=GatewayRejected("no", code=-51)))
    _initiate(user)

    payment = services.verify_payment(authority="A123", callback_status="OK")

    assert payment.status == PaymentStatus.FAILED
    assert WalletTransaction.objects.count() == 0


def test_unavailable_gateway_keeps_payment_pending(user, use_gateway):
    use_gateway(FakeGateway(verify_exc=GatewayUnavailable("down")))
    _initiate(user)

    with pytest.raises(GatewayUnavailable):
        services.verify_payment(authority="A123", callback_status="OK")

    assert Payment.objects.get(authority="A123").status == PaymentStatus.PENDING
    assert WalletTransaction.objects.count() == 0


def test_gateway_failure_on_initiate_leaves_failed_row(user, use_gateway):
    use_gateway(FakeGateway(request_exc=GatewayRejected("no", code=-9)))

    with pytest.raises(GatewayRejected):
        _initiate(user)

    assert Payment.objects.get().status == PaymentStatus.FAILED