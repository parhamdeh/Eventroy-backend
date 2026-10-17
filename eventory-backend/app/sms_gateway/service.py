"""Application-facing messaging service used by Celery tasks and callers."""

from __future__ import annotations

from app.sms_gateway.factory import MessageSenderFactory
from app.sms_gateway.interfaces import MessagePayload


class MessagingService:
    """Select a strategy and send a message. Auth code depends only on this API."""

    def __init__(self, factory: MessageSenderFactory | None = None) -> None:
        self._factory = factory or MessageSenderFactory()

    def send(
        self,
        *,
        channel: str,
        recipient: str,
        template: str,
        context: dict[str, object] | None = None,
        subject: str | None = None,
    ) -> None:
        """Deliver a message on `channel` to `recipient`."""

        sender = self._factory.get(channel)
        payload = MessagePayload(template=template, context=context or {}, subject=subject)
        sender.send(recipient, payload)
