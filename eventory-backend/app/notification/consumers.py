from channels.generic.websocket import AsyncJsonWebsocketConsumer

from app.notification.services import user_group

UNAUTHENTICATED_CLOSE_CODE = 4401


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Server -> client stream of events for one user.

    Frames look like {"event": "wallet.balance", "payload": {...}}.
    The only message the client may send is {"action": "ping"}.
    """

    group_name: str | None = None

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            # Accept first so the browser can actually read close code 4401
            # (closing before accept is shown to clients as a bare HTTP 403).
            await self.accept()
            await self.close(code=UNAUTHENTICATED_CLOSE_CODE)
            return

        self.group_name = user_group(user.pk)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"event": "connected", "payload": {}})

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if isinstance(content, dict) and content.get("action") == "ping":
            await self.send_json({"event": "pong", "payload": {}})
        # everything else is ignored on purpose

    # Handler for channel-layer messages with type "notify.event"
    async def notify_event(self, message):
        await self.send_json(
            {"event": message["event"], "payload": message["payload"]}
        )