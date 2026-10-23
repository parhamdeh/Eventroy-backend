"""Email adapter using Django's configured email backend."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from app.sms_gateway.content import render_email
from app.sms_gateway.exceptions import PermanentDeliveryError, RetryableDeliveryError
from app.sms_gateway.interfaces import MessagePayload, MessageSender

logger = logging.getLogger(__name__)


class EmailSender(MessageSender):
    """Send email through Django's `EMAIL_BACKEND`."""

    channel = "email"

    def send(self, recipient: str, payload: MessagePayload) -> None:
        """Validate the address and send the rendered email."""

        if not recipient or "@" not in recipient:
            raise PermanentDeliveryError("Email recipient is invalid.")

        subject, body = render_email(payload.template, payload.context)
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "parhamdehghan1385@gmail.com")

        try:
            sent = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[recipient.strip().lower()],
                fail_silently=False,
            )
        except (TimeoutError, ConnectionError, OSError) as exc:
            logger.warning("Email transport failure for recipient=%s", recipient)
            raise RetryableDeliveryError("Email transport error.") from exc
        except Exception as exc:
            logger.warning("Email backend rejected message for recipient=%s", recipient)
            raise PermanentDeliveryError("Email backend rejected the message.") from exc

        if not sent:
            raise RetryableDeliveryError("Email backend reported zero messages sent.")

        logger.info("Email sent to recipient=%s template=%s", recipient, payload.template)
