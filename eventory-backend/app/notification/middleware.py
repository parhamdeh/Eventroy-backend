from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from app.notification.services import consume_ws_ticket


@database_sync_to_async
def _user_from_scope(scope):
    query = parse_qs(scope.get("query_string", b"").decode())
    ticket = (query.get("ticket") or [None])[0]
    if not ticket:
        return AnonymousUser()

    user_id = consume_ws_ticket(ticket)
    if user_id is None:
        return AnonymousUser()

    user = get_user_model().objects.filter(pk=user_id, is_active=True).first()
    return user or AnonymousUser()


class TicketAuthMiddleware(BaseMiddleware):
    """Authenticate a WebSocket with a single-use ticket and set scope['user']."""

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["user"] = await _user_from_scope(scope)
        return await super().__call__(scope, receive, send)