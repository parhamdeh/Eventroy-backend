import logging
from dataclasses import dataclass
from functools import partial

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from app.payment_gateway.enums import PaymentPurpose, PaymentStatus
from app.payment_gateway.exception import (
    GatewayError,
    GatewayRejected,
    PaymentNotFound,
)
from app.payment_gateway.gateways.registry import get_gateway
from app.notification.enums import NotificationKind
from app.notification.services import create_notification
from app.payment_gateway.models import Payment
from app.users.models import WalletTransaction
from app.users.services import credit_wallet

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InitiatedPayment:
    payment_id: int
    authority: str
    payment_url: str


# --------------------------------------------------------------------------
# Initiate
# --------------------------------------------------------------------------
def initiate_wallet_charge(*, user, amount: int) -> InitiatedPayment:
    """
    Create a PENDING payment and ask the gateway for a payment session.

    The DB row is committed BEFORE the HTTP call: we never hold a
    transaction open across the network, and if the gateway fails we
    keep an auditable FAILED row instead of an orphan PENDING one.
    """
    gateway_name = settings.PAYMENT_DEFAULT_GATEWAY
    gateway = get_gateway(gateway_name)

    payment = Payment.objects.create(
        user=user,
        amount=amount,
        purpose=PaymentPurpose.WALLET_CHARGE,
        gateway=gateway_name,
    )

    try:
        result = gateway.request(
            amount=payment.amount,
            description=f"شارژ کیف پول #{payment.pk}",
            callback_url=settings.PAYMENT_CALLBACK_URL,
            mobile=getattr(user, "phone", None),
        )
    except GatewayError as exc:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = str(exc)[:255]
        payment.save(update_fields=["status", "failure_reason", "updated_at"])
        raise

    payment.authority = result.authority
    payment.save(update_fields=["authority", "updated_at"])

    return InitiatedPayment(
        payment_id=payment.pk,
        authority=result.authority,
        payment_url=result.payment_url,
    )


# --------------------------------------------------------------------------
# Fulfilment (what happens once money is confirmed)
# --------------------------------------------------------------------------
def _fulfill_wallet_charge(payment: Payment) -> None:
    credit_wallet(
        user_id=payment.user_id,
        amount=payment.amount,
        kind=WalletTransaction.Kind.CHARGE,
        # Same payment => same key => can never be credited twice.
        idempotency_key=f"payment:{payment.pk}",
        description=f"Wallet charge via {payment.gateway} (ref {payment.ref_id})",
    )


_FULFILLERS = {
    PaymentPurpose.WALLET_CHARGE: _fulfill_wallet_charge,
}


def _notify_payment_success(payment: Payment) -> None:
    """Best-effort inbox entry; must never affect an already settled payment."""
    try:
        create_notification(
            user_id=payment.user_id,
            kind=NotificationKind.WALLET_CHARGED,
            title="شارژ کیف پول موفق",
            body=f"{payment.amount:,} تومان به کیف پول شما اضافه شد.",
            data={
                "payment_id": str(payment.pk),
                "ref_id": payment.ref_id,
                "amount": payment.amount,
            },
        )
    except Exception:  # noqa: BLE001
        logger.exception("Could not create notification for payment %s", payment.pk)


# --------------------------------------------------------------------------
# Verify (gateway callback)
# --------------------------------------------------------------------------
def verify_payment(*, authority: str, callback_status: str) -> Payment:
    """
    Settle a payment after the user comes back from the gateway.

    Safe to call any number of times, concurrently, for the same
    authority: the row is locked, and anything that is no longer PENDING
    is returned untouched.

    Raises:
        PaymentNotFound:    unknown authority.
        GatewayUnavailable: outcome unknown; payment stays PENDING so the
                            callback can be retried safely.
    """
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(authority=authority)
        except Payment.DoesNotExist:
            raise PaymentNotFound("Unknown payment.") from None

        if payment.status != PaymentStatus.PENDING:
            return payment  # replay: nothing to do

        if callback_status != "OK":
            payment.status = PaymentStatus.CANCELED
            payment.save(update_fields=["status", "updated_at"])
            return payment

        gateway = get_gateway(payment.gateway)
        try:
            # Always verify with OUR stored amount, never anything from the request.
            result = gateway.verify(authority=authority, amount=payment.amount)
        except GatewayRejected as exc:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = f"{exc} (code={exc.code})"[:255]
            payment.save(update_fields=["status", "failure_reason", "updated_at"])
            return payment
        # GatewayUnavailable propagates: transaction rolls back, status stays PENDING.

        payment.status = PaymentStatus.SUCCESS
        payment.ref_id = result.ref_id
        payment.card_pan = result.card_pan
        payment.gateway_fee = result.fee
        payment.paid_at = timezone.now()
        payment.save(
            update_fields=[
                "status", "ref_id", "card_pan", "gateway_fee", "paid_at", "updated_at",
            ]
        )

        # Same transaction as the status change: either both happen or neither.
        _FULFILLERS[payment.purpose](payment)
        transaction.on_commit(partial(_notify_payment_success, payment))

    logger.info("Payment %s verified (ref %s)", payment.pk, payment.ref_id)
    return payment