from django.conf import settings
from django.db import models

from app.common.models import BaseModel
from app.payment_gateway.enums import PaymentGatewayName, PaymentPurpose, PaymentStatus


class Payment(BaseModel):
    """
    One attempt to pay through an online gateway. Amounts are integer tomans.

    A payment moves PENDING -> SUCCESS | FAILED | CANCELED | EXPIRED and
    never leaves a terminal state; that rule is what makes callbacks
    safe to replay.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.PositiveBigIntegerField(help_text="Amount in tomans.")
    purpose = models.CharField(max_length=30, choices=PaymentPurpose.choices)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    gateway = models.CharField(
        max_length=30,
        choices=PaymentGatewayName.choices,
        default=PaymentGatewayName.ZARINPAL,
    )
    # unique already creates an index; null is allowed until the gateway answers.
    authority = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )
    ref_id = models.CharField(max_length=100, blank=True)
    card_pan = models.CharField(max_length=32, blank=True)
    gateway_fee = models.PositiveBigIntegerField(default=0)
    failure_reason = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["status", "created_at"], name="payment_status_created_idx"
            ),
            models.Index(
                fields=["user", "-created_at"], name="payment_user_created_idx"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="payment_amount_positive"
            ),
        ]

    def __str__(self) -> str:
        return f"Payment #{self.pk} [{self.status}]"