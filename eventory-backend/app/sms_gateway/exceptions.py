"""Messaging delivery errors distinguished by retryability."""

from __future__ import annotations


class MessagingError(Exception):
    """Base error for message delivery failures."""

    retryable: bool = False

    def __init__(self, message: str, *, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class RetryableDeliveryError(MessagingError):
    """Transient provider or network failure that Celery may retry."""

    retryable = True


class PermanentDeliveryError(MessagingError):
    """Non-retryable failure such as an invalid recipient."""

    retryable = False
