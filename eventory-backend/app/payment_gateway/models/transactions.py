
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from app.common.models import BaseModel
from app.payment_gateway.enums import (
    GatewayType,
    PaymentStatus,
    PaymentType,
)


class Transaction(BaseModel):
    """
    Represent a payment attempt and its lifecycle.

    Monetary amounts are stored as integer Iranian rials to match
    the payment gateway's expected unit. Conversion to tomans must
    happen explicitly when interacting with a wallet using tomans.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("transaction ID"),
        help_text=_("Unique public identifier for this transaction."),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("user"),
        help_text=_("The user who initiated the transaction."),
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        verbose_name=_("transaction type"),
        help_text=_("The purpose of the payment."),
    )

    order = models.ForeignKey(
        "users.OrderModel",
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
        verbose_name=_("order"),
        help_text=_("The associated order, if this payment is for an order."),
    )

    gateway = models.CharField(
        max_length=32,
        choices=GatewayType.choices,
        default=GatewayType.ZARINPAL,
        verbose_name=_("payment gateway"),
        help_text=_("The gateway used to process the payment."),
    )

    authority = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("gateway authority"),
        help_text=_("The payment authority returned by the gateway."),
    )

    ref_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("gateway reference ID"),
        help_text=_("The reference ID returned after successful verification."),
    )

    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name=_("status"),
        help_text=_("The current payment status."),
    )

    total_amount = models.PositiveBigIntegerField(
        verbose_name=_("total amount"),
        help_text=_("The total payment amount in Iranian rials."),
    )

    idempotency_key = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("idempotency key"),
        help_text=_(
            "Optional unique key used to prevent duplicate payment creation."
        ),
    )

    raw_callback_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("raw callback data"),
        help_text=_("The callback payload received from the gateway."),
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("metadata"),
        help_text=_("Additional non-sensitive payment information."),
    )

    failure_reason = models.TextField(
        blank=True,
        default="",
        verbose_name=_("failure reason"),
        help_text=_("A safe diagnostic description of the payment failure."),
    )

    callback_received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("callback received at"),
        help_text=_("When the gateway callback was received."),
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("verified at"),
        help_text=_("When the gateway successfully verified the payment."),
    )

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="txn_user_created_idx",
            ),
            models.Index(
                fields=["status", "-created_at"],
                name="txn_status_created_idx",
            ),
            models.Index(
                fields=["gateway", "status"],
                name="txn_gateway_status_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gt=0),
                name="txn_amount_gt_zero",
            ),
            models.UniqueConstraint(
                fields=["gateway", "authority"],
                condition=~Q(authority=""),
                name="txn_gateway_authority_uniq",
            ),
            models.UniqueConstraint(
                fields=["gateway", "ref_id"],
                condition=~Q(ref_id=""),
                name="txn_gateway_ref_id_uniq",
            ),
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="txn_user_idempotency_uniq",
            ),
        ]

    def clean(self) -> None:
        """Validate transaction-specific business rules."""
        super().clean()

        if self.transaction_type == PaymentType.ORDER and not self.order_id:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                {"order": _("An order is required for order payments.")}
            )

        if (
            self.transaction_type == PaymentType.WALLET_CHARGE
            and self.order_id
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError(
                {"order": _("Wallet charges cannot be linked to an order.")}
            )

    def __str__(self) -> str:
        return (
            f"Transaction(id={self.pk}, "
            f"type={self.transaction_type}, "
            f"amount={self.total_amount}, "
            f"status={self.status})"
        )
