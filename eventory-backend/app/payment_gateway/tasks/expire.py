from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from app.payment_gateway.enums import PaymentStatus
from app.payment_gateway.models import Payment


@shared_task
def expire_stale_payments() -> int:
    """
    Close PENDING payments that were abandoned (user never came back).
    Schedule every ~10 minutes with celery-beat.

    A single conditional UPDATE: if a callback is verifying a row right
    now, Postgres re-checks `status=PENDING` after its lock is released,
    so we can never overwrite a payment that just succeeded.
    """
    cutoff = timezone.now() - timedelta(minutes=settings.PAYMENT_PENDING_TTL_MINUTES)
    return Payment.objects.filter(
        status=PaymentStatus.PENDING,
        created_at__lt=cutoff,
    ).update(status=PaymentStatus.EXPIRED, failure_reason="expired")