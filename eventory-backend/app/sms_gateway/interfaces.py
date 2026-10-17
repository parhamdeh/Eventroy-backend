"""Strategy interface and payload types for outbound messages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MessagePayload:
    """Provider-independent description of a message to send."""

    template: str
    context: dict[str, Any] = field(default_factory=dict)
    subject: str | None = None


class MessageSender(ABC):
    """Strategy for delivering a message on one channel."""

    channel: str

    @abstractmethod
    def send(self, recipient: str, payload: MessagePayload) -> None:
        """
        Deliver `payload` to `recipient`.

        Raises:
            RetryableDeliveryError: Transient failure; Celery may retry.
            PermanentDeliveryError: Invalid recipient or payload.
        """
