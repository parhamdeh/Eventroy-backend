from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.common.models import BaseModel


class Wallet(BaseModel):
    """
    Represent a user's wallet and its current monetary balance.

    The balance is stored as an integer in Iranian tomans.
    Each user can have only one wallet.

    NEVER mutate ``balance`` outside ``wallets.services``: every change
    must go through credit_wallet / debit_wallet so that a ledger row
    (WalletTransaction) is written in the same DB transaction.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wallet",
        verbose_name=_("user"),
        help_text=_("The user who owns this wallet."),
    )

    balance = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_("balance"),
        help_text=_("The current wallet balance in Iranian tomans."),
    )

    card_number = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        verbose_name=_("card number"),
        help_text=_("The user's bank card number. This field is optional."),
    )

    class Meta:
        verbose_name = _("wallet")
        verbose_name_plural = _("wallets")

    def __str__(self) -> str:
        return f"Wallet(user_id={self.user_id}, balance={self.balance})"


class WalletTransaction(BaseModel):
    """
    Immutable ledger entry: one row per balance change.

    ``idempotency_key`` is unique, so the same business event (for
    example ``payment:42``) can never be applied to a wallet twice,
    even if application-level checks are bypassed or raced.
    """

    class Kind(models.TextChoices):
        CHARGE = "CHARGE", _("Charge")
        PURCHASE = "PURCHASE", _("Purchase")
        REFUND = "REFUND", _("Refund")
        ADJUSTMENT = "ADJUSTMENT", _("Adjustment")

    class Direction(models.TextChoices):
        CREDIT = "CREDIT", _("Credit")
        DEBIT = "DEBIT", _("Debit")

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("wallet"),
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount = models.PositiveBigIntegerField(
        help_text=_("Always positive; the sign comes from `direction`."),
    )
    balance_after = models.PositiveBigIntegerField(
        help_text=_("Wallet balance right after this entry was applied."),
    )
    idempotency_key = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = _("wallet transaction")
        verbose_name_plural = _("wallet transactions")
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["wallet", "-created_at"],
                name="wallettx_wallet_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="wallettx_amount_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.direction} {self.amount} ({self.kind})"