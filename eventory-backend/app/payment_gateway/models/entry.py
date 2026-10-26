
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from app.common.models import BaseModel
from app.payment_gateway.enums import EntryType
from app.payment_gateway.models.transactions import Transaction


class TransactionEntry(BaseModel):
    """
    Represent a financial component of a transaction.

    Entries are immutable after creation. Financial corrections should
    be recorded through compensating entries or a separate correction
    transaction rather than editing historical records.
    """

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name=_("transaction"),
        help_text=_("The transaction to which this entry belongs."),
    )

    entry_type = models.CharField(
        max_length=16,
        choices=EntryType.choices,
        verbose_name=_("entry type"),
        help_text=_("The financial category of this entry."),
    )

    amount = models.PositiveBigIntegerField(
        verbose_name=_("amount"),
        help_text=_("The entry amount in Iranian rials."),
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("description"),
        help_text=_("An optional description of the entry."),
    )

    class Meta:
        verbose_name = _("transaction entry")
        verbose_name_plural = _("transaction entries")
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="txn_entry_amount_gt_zero",
            ),
            models.UniqueConstraint(
                fields=["transaction", "entry_type"],
                name="txn_entry_type_per_transaction_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["transaction", "entry_type"],
                name="txn_entry_type_idx",
            ),
        ]

    def save(self, *args, **kwargs) -> None:
        """Prevent updates to an existing financial entry."""
        if not self._state.adding:
            raise ValidationError(
                _("Transaction entries cannot be modified after creation.")
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of historical financial entries."""
        raise ValidationError(
            _("Transaction entries cannot be deleted.")
        )

    def __str__(self) -> str:
        return (
            f"TransactionEntry(transaction_id={self.transaction_id}, "
            f"type={self.entry_type}, amount={self.amount})"
        )
