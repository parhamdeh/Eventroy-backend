import logging
import secrets
from functools import partial

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from app.notification.enums import NotificationKind
from app.notification.models import Notification

logger = logging.getLogger(__name__)

_TICKET_PREFIX = "ws_ticket:"


# --------------------------------------------------------------------------
# Real-time push
# --------------------------------------------------------------------------
def user_group(user_id) -> str:
    """One channel-layer group per user; every open tab/device joins it."""
    return f"user_{user_id}"


def push_event(*, user_id, event: str, payload: dict) -> None:
    """
    Send `{"event": ..., "payload": ...}` to every WebSocket of the user.

    Best-effort by design: if Redis is down or nobody is connected the
    business flow (payment, order, ...) must not fail. Call it from
    transaction.on_commit when it follows a DB change.

    Must be called from sync code (views, services, Celery). In async
    code wrap it with sync_to_async.
    """
    layer = get_channel_layer()
    if layer is None:
        logger.warning("No channel layer configured; dropped event %s", event)
        return
    try:
        async_to_sync(layer.group_send)(
            user_group(user_id),
            {"type": "notify.event", "event": event, "payload": payload},
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to push %s to user %s", event, user_id)


# --------------------------------------------------------------------------
# Persisted notifications
# --------------------------------------------------------------------------
def _serialize(notification: Notification) -> dict:
    return {
        "id": str(notification.pk),
        "kind": notification.kind,
        "title": notification.title,
        "body": notification.body,
        "data": notification.data,
        "created_at": notification.created_at.isoformat(),
    }


def create_notification(
    *,
    user_id,
    title: str,
    body: str = "",
    kind: str = NotificationKind.SYSTEM,
    data: dict | None = None,
) -> Notification:
    """Store a notification and push it live once the DB transaction commits."""
    notification = Notification.objects.create(
        user_id=user_id,
        kind=kind,
        title=title,
        body=body,
        data=data or {},
    )
    transaction.on_commit(
        partial(
            push_event,
            user_id=user_id,
            event="notification.new",
            payload=_serialize(notification),
        )
    )
    return notification


def mark_notification_read(*, notification: Notification) -> None:
    if notification.is_read:
        return
    Notification.objects.filter(pk=notification.pk, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def mark_all_read(*, user) -> int:
    return Notification.objects.filter(user=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def unread_count(*, user) -> int:
    return Notification.objects.filter(user=user, is_read=False).count()


# --------------------------------------------------------------------------
# WebSocket tickets
#
# Browsers cannot set an Authorization header on a WebSocket, and putting
# the JWT in the URL leaks it into proxy/access logs. Instead the client
# calls an authenticated REST endpoint, gets a random single-use ticket
# valid for a few seconds, and connects with ?ticket=...
# The cache MUST be shared between processes (Redis), not locmem.
# --------------------------------------------------------------------------
def issue_ws_ticket(*, user_id) -> str:
    ticket = secrets.token_urlsafe(32)
    cache.set(
        f"{_TICKET_PREFIX}{ticket}",
        str(user_id),
        timeout=settings.NOTIFICATION_WS_TICKET_TTL,
    )
    return ticket


def consume_ws_ticket(ticket: str) -> str | None:
    """Return the user id for a valid ticket and burn it. None otherwise."""
    key = f"{_TICKET_PREFIX}{ticket}"
    user_id = cache.get(key)
    # delete() returns True only for the caller that actually removed it,
    # so two parallel connects with the same ticket can't both win.
    if user_id is None or not cache.delete(key):
        return None
    return user_id