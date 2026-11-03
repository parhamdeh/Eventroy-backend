# config/asgi.py
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # <- your real path

# Must run BEFORE importing anything that touches models/consumers.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from app.notification.middleware import TicketAuthMiddleware  # noqa: E402
from app.notification.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Origin check blocks cross-site WebSocket hijacking; the ticket
        # middleware authenticates the user.
        "websocket": AllowedHostsOriginValidator(
            TicketAuthMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)