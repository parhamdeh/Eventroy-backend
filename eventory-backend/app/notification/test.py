"""
Needs: pytest-django, pytest-asyncio and a `user` fixture in your conftest.
Uses the in-memory channel layer + default cache, so no Redis is required.
"""
import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import path

from app.notification.consumers import (
    UNAUTHENTICATED_CLOSE_CODE,
    NotificationConsumer,
)
from app.notification.middleware import TicketAuthMiddleware
from app.notification.services import issue_ws_ticket, push_event

application = TicketAuthMiddleware(
    URLRouter([path("ws/notifications/", NotificationConsumer.as_asgi())])
)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def _in_memory_layer(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
    settings.NOTIFICATION_WS_TICKET_TTL = 30


def _communicator(ticket: str | None):
    suffix = f"?ticket={ticket}" if ticket else ""
    return WebsocketCommunicator(application, f"/ws/notifications/{suffix}")


async def test_valid_ticket_connects_and_receives_pushed_event(user):
    ticket = issue_ws_ticket(user_id=user.pk)
    comm = _communicator(ticket)

    connected, _ = await comm.connect()
    assert connected
    assert (await comm.receive_json_from())["event"] == "connected"

    await sync_to_async(push_event)(
        user_id=user.pk, event="wallet.balance", payload={"balance": 1000}
    )
    assert await comm.receive_json_from() == {
        "event": "wallet.balance",
        "payload": {"balance": 1000},
    }
    await comm.disconnect()


async def test_missing_or_invalid_ticket_is_closed_with_4401():
    for ticket in (None, "not-a-real-ticket"):
        comm = _communicator(ticket)
        connected, _ = await comm.connect()
        assert connected  # accepted first so the client can read the code
        message = await comm.receive_output()
        assert message["type"] == "websocket.close"
        assert message["code"] == UNAUTHENTICATED_CLOSE_CODE


async def test_ticket_is_single_use(user):
    ticket = issue_ws_ticket(user_id=user.pk)

    first = _communicator(ticket)
    await first.connect()
    assert (await first.receive_json_from())["event"] == "connected"

    second = _communicator(ticket)
    await second.connect()
    assert (await second.receive_output())["type"] == "websocket.close"
    await first.disconnect()


async def test_events_are_not_delivered_to_other_users(user):
    ticket = issue_ws_ticket(user_id=user.pk)
    comm = _communicator(ticket)
    await comm.connect()
    await comm.receive_json_from()  # "connected"

    await sync_to_async(push_event)(
        user_id="someone-else", event="wallet.balance", payload={"balance": 1}
    )
    assert await comm.receive_nothing()
    await comm.disconnect()