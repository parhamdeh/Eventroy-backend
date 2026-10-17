"""Factory/registry that resolves a MessageSender by channel and provider."""

from __future__ import annotations

from django.conf import settings

from app.sms_gateway.interfaces import MessageSender
from app.sms_gateway.strategies.email import EmailSender
from app.sms_gateway.strategies.kavenegar import KavenegarSmsSender

_SMS_PROVIDERS: dict[str, type[MessageSender]] = {
    "kavenegar": KavenegarSmsSender,
}

_CHANNEL_SENDERS: dict[str, type[MessageSender]] = {
    "email": EmailSender,
}


def register_sms_provider(name: str, sender_cls: type[MessageSender]) -> None:
    """Register an additional SMS provider without changing auth workflows."""

    _SMS_PROVIDERS[name] = sender_cls


class MessageSenderFactory:
    """Return the configured strategy for a logical channel (`sms` or `email`)."""

    def get(self, channel: str) -> MessageSender:
        """
        Resolve a sender.

        `phone` is treated as `sms` so authentication code can speak in
        identifier-channel terms.
        """

        normalized = "sms" if channel in {"sms", "phone"} else channel
        if normalized == "sms":
            provider = getattr(settings, "SMS_PROVIDER", "kavenegar")
            try:
                sender_cls = _SMS_PROVIDERS[provider]
            except KeyError as exc:
                raise ValueError(f"Unknown SMS provider: {provider}") from exc
            return sender_cls()

        try:
            sender_cls = _CHANNEL_SENDERS[normalized]
        except KeyError as exc:
            raise ValueError(f"Unknown messaging channel: {channel}") from exc
        return sender_cls()
