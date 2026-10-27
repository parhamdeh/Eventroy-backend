from django.urls import path

from app.notification import apis

app_name = "notifications"

urlpatterns = [
    path("", apis.NotificationListAPI.as_view(), name="list"),
    path("unread-count/", apis.UnreadCountAPI.as_view(), name="unread-count"),
    path("read-all/", apis.MarkAllReadAPI.as_view(), name="read-all"),
    path("ws-ticket/", apis.WsTicketAPI.as_view(), name="ws-ticket"),
    path("<str:pk>/read/", apis.MarkReadAPI.as_view(), name="read"),
]