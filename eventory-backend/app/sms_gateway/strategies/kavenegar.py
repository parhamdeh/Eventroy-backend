"""Kavenegar SMS adapter. Provider details stay inside this module."""

from __future__ import annotations

import logging

from django.conf import settings

from app.sms_gateway.content import render_sms
from app.sms_gateway.exceptions import PermanentDeliveryError, RetryableDeliveryError
from app.sms_gateway.interfaces import MessagePayload, MessageSender

logger = logging.getLogger(__name__)


class KavenegarSmsSender(MessageSender):
    """Send SMS messages through the Kavenegar HTTP API."""

    channel = "sms"

    def send(self, recipient: str, payload: MessagePayload) -> None:
        """Validate the recipient and dispatch the rendered SMS body."""

        if not recipient or not str(recipient).strip():
            raise PermanentDeliveryError("SMS recipient is required.")

        api_key = getattr(settings, "KAVENEGAR_API_KEY", "") or ""
        if not api_key:
            raise PermanentDeliveryError("Kavenegar API key is not configured.")

        body = render_sms(payload.template, payload.context)
        sender = getattr(settings, "KAVENEGAR_SENDER", "") or None

        try:
            from kavenegar import APIException, HTTPException, KavenegarAPI
        except ImportError as exc:
            raise PermanentDeliveryError("Kavenegar SDK is not installed.") from exc

        params: dict[str, str] = {"receptor": recipient.strip(), "message": body}
        if sender:
            params["sender"] = sender

        try:
            api = KavenegarAPI(api_key)
            api.sms_send(params)
        except HTTPException as exc:
            logger.warning("Kavenegar HTTP failure for receptor=%s", recipient)
            raise RetryableDeliveryError("Kavenegar HTTP error.") from exc
        except APIException as exc:
            message = str(exc)
            if _is_retryable_kavenegar(message):
                logger.warning("Kavenegar retryable API failure for receptor=%s", recipient)
                raise RetryableDeliveryError("Kavenegar API error.") from exc
            logger.warning("Kavenegar permanent API failure for receptor=%s", recipient)
            raise PermanentDeliveryError("Kavenegar rejected the message.") from exc
        except (TimeoutError, ConnectionError, OSError) as exc:
            logger.warning("Kavenegar network failure for receptor=%s", recipient)
            raise RetryableDeliveryError("Kavenegar network error.") from exc

        logger.info("SMS queued with Kavenegar for receptor=%s template=%s", recipient, payload.template)


def _is_retryable_kavenegar(message: str) -> bool:
    """Treat rate-limit and 5xx-style Kavenegar errors as retryable."""

    lowered = message.lower()
    return any(token in lowered for token in ("timeout", "429", "500", "502", "503", "504"))
