"""Celery tasks for asynchronous message delivery."""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from django.core.cache import cache

from app.sms_gateway.exceptions import PermanentDeliveryError, RetryableDeliveryError
from app.sms_gateway.service import MessagingService

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3


@shared_task(
    bind=True,
    name="app.sms_gateway.tasks.deliver_message",
    max_retries=_MAX_RETRIES,
    autoretry_for=(RetryableDeliveryError,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def deliver_message(
    self,
    *,
    channel: str,
    recipient: str,
    template: str,
    context: dict[str, Any] | None = None,
    subject: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    """
    Deliver a message asynchronously.

    OTP plaintext must not be passed here. Callers store a short-lived delivery
    payload in cache and put the cache key in `context['delivery_key']`.
    """

    if idempotency_key:
        marker = cache.get(idempotency_key)
        if marker == "sent":
            logger.info("Skipping duplicate delivery idempotency_key=%s", idempotency_key)
            return

    payload_context = dict(context or {})
    delivery_key = payload_context.pop("delivery_key", None)
    if delivery_key:
        code = cache.get(delivery_key)
        if not code:
            logger.info("Delivery payload expired for template=%s", template)
            return
        payload_context["code"] = code

    try:
        MessagingService().send(
            channel=channel,
            recipient=recipient,
            template=template,
            context=payload_context,
            subject=subject,
        )
    except PermanentDeliveryError:
        logger.warning("Permanent delivery failure channel=%s template=%s", channel, template)
        raise
    except RetryableDeliveryError:
        logger.warning(
            "Retryable delivery failure channel=%s template=%s retries=%s",
            channel,
            template,
            self.request.retries,
        )
        raise

    if delivery_key:
        cache.delete(delivery_key)
    if idempotency_key:
        cache.set(idempotency_key, "sent", timeout=300)
