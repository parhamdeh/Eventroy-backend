from django.conf import settings
from django.db import models

from app.common.models import BaseModel
from app.notification.enums import NotificationKind


class Notification(BaseModel):
    """
    A persisted, user-facing notification (the in-app inbox).

    Pure real-time signals such as "wallet balance changed" are NOT
    stored; they are only pushed over the WebSocket (see services.push_event).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(
        max_length=30,
        choices=NotificationKind.choices,
        default=NotificationKind.SYSTEM,
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["user", "is_read", "-created_at"],
                name="notif_user_read_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Notification({self.kind}) -> user {self.user_id}"