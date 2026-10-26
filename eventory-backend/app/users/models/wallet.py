from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from app.common.models import BaseModel


class Wallet(BaseModel):
    """
    Represent a user's wallet and its current monetary balance.

    The balance is stored as an integer in Iranian tomans.
    Each user can have only one wallet.
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
        validators=[
            RegexValidator(
                regex=r"^\d{16}$",
                message=_("The card number must contain exactly 16 digits."),
            )
        ],
        verbose_name=_("card number"),
        help_text=_("Optional bank card number."),
    )

    class Meta:
        """Define wallet model metadata."""

        verbose_name = _("wallet")
        verbose_name_plural = _("wallets")

    def __str__(self) -> str:
        """Return a readable representation of the wallet."""
        return (
            f"Wallet(user_id={self.user_id}, "
            f"balance={self.balance})"
        )
