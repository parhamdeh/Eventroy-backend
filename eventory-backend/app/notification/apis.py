from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.notification.models import Notification
from app.notification.serializers import (
    NotificationSerializer,
    UnreadCountSerializer,
    WsTicketSerializer,
)
from app.notification.services import (
    issue_ws_ticket,
    mark_all_read,
    mark_notification_read,
    unread_count,
)
from app.notification.throttles import WsTicketThrottle


class NotificationListAPI(ListAPIView):
    """Newest first, uses your project's default pagination."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @extend_schema(
        tags=["Notification"],
        summary="List my notifications",
        parameters=[OpenApiParameter("unread", bool, description="Only unread ones.")],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread", "").lower() in ("1", "true"):
            qs = qs.filter(is_read=False)
        return qs


class UnreadCountAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notification"],
        summary="Number of unread notifications",
        responses=UnreadCountSerializer,
    )
    def get(self, request):
        return Response({"unread": unread_count(user=request.user)})


class MarkReadAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notification"],
        summary="Mark one notification as read",
        request=None,
        responses={204: None},
    )
    def post(self, request, pk):
        try:
            # Scoped to the requester: other users' ids are simply "not found".
            notification = Notification.objects.get(pk=pk, user=request.user)
        except (Notification.DoesNotExist, ValueError, DjangoValidationError):
            raise Http404 from None
        mark_notification_read(notification=notification)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkAllReadAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notification"],
        summary="Mark all notifications as read",
        request=None,
        responses={204: None},
    )
    def post(self, request):
        mark_all_read(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WsTicketAPI(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [WsTicketThrottle]

    @extend_schema(
        tags=["Notification"],
        summary="Get a single-use ticket to open the notifications WebSocket",
        request=None,
        responses=WsTicketSerializer,
    )
    def post(self, request):
        return Response(
            {
                "ticket": issue_ws_ticket(user_id=request.user.pk),
                "expires_in": settings.NOTIFICATION_WS_TICKET_TTL,
            }
        )