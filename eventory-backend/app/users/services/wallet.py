def create_wallet(*, user: User):
    return Wallet.objects.create(
        user=user
    )
from app.users.models import Wallet, User, WalletTransaction
from functools import partial

from django.db import models, transaction
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce

from app.users.exceptions import InsufficientBalance, InvalidAmount
from app.payment_gateway.notification import notify_balance_changed

Kind = WalletTransaction.Kind
Direction = WalletTransaction.Direction


def _validate_amount(amount: int) -> None:
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise InvalidAmount("Amount must be a positive integer.")


def _lock_wallet(user_id: int) -> Wallet:
    """Return the user's wallet locked FOR UPDATE (creating it if missing)."""
    wallet, _ = Wallet.objects.get_or_create(user_id=user_id)
    return Wallet.objects.select_for_update().get(pk=wallet.pk)


def _apply(
    *,
    user_id: int,
    amount: int,
    kind: str,
    direction: str,
    idempotency_key: str,
    description: str,
) -> WalletTransaction:
    _validate_amount(amount)

    with transaction.atomic():
        wallet = _lock_wallet(user_id)

        # Idempotent replay: same event => same ledger row, no second effect.
        existing = WalletTransaction.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        if existing is not None:
            return existing

        if direction == Direction.DEBIT:
            if wallet.balance < amount:
                raise InsufficientBalance("Insufficient wallet balance.")
            wallet.balance -= amount
        else:
            wallet.balance += amount

        # Safe as a plain read-modify-write: the row is locked above.
        wallet.save()

        entry = WalletTransaction.objects.create(
            wallet=wallet,
            kind=kind,
            direction=direction,
            amount=amount,
            balance_after=wallet.balance,
            idempotency_key=idempotency_key,
            description=description[:255],
        )

        transaction.on_commit(
            partial(
                notify_balance_changed,
                user_id=user_id,
                balance=wallet.balance,
            )
        )
        return entry


def credit_wallet(
    *,
    user_id: int,
    amount: int,
    kind: str = Kind.CHARGE,
    idempotency_key: str,
    description: str = "",
) -> WalletTransaction:
    """Add `amount` tomans to the wallet. Idempotent per `idempotency_key`."""
    return _apply(
        user_id=user_id,
        amount=amount,
        kind=kind,
        direction=Direction.CREDIT,
        idempotency_key=idempotency_key,
        description=description,
    )


def debit_wallet(
    *,
    user_id: int,
    amount: int,
    kind: str = Kind.PURCHASE,
    idempotency_key: str,
    description: str = "",
) -> WalletTransaction:
    """
    Remove `amount` tomans from the wallet.

    Raises InsufficientBalance if the balance is too low. Call this from
    your order service inside the same transaction that marks the order
    as paid, so both succeed or both roll back.
    """
    return _apply(
        user_id=user_id,
        amount=amount,
        kind=kind,
        direction=Direction.DEBIT,
        idempotency_key=idempotency_key,
        description=description,
    )


def calculate_ledger_balance(*, wallet_id) -> int:
    """
    Balance implied by the ledger: sum(credits) - sum(debits).

    This is the source of truth. Wallet.balance is just a cached copy of
    it, kept for fast reads and row-level locking.
    """
    zero = Value(0, output_field=models.BigIntegerField())
    totals = WalletTransaction.objects.filter(wallet_id=wallet_id).aggregate(
        credits=Coalesce(
            Sum("amount", filter=Q(direction=Direction.CREDIT)),
            zero,
            output_field=models.BigIntegerField(),
        ),
        debits=Coalesce(
            Sum("amount", filter=Q(direction=Direction.DEBIT)),
            zero,
            output_field=models.BigIntegerField(),
        ),
    )
    return totals["credits"] - totals["debits"]