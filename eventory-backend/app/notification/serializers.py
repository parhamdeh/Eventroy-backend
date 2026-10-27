from rest_framework import serializers

from app.notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "kind", "title", "body", "data", "is_read", "created_at")
        read_only_fields = fields


class UnreadCountSerializer(serializers.Serializer):
    unread = serializers.IntegerField()


class WsTicketSerializer(serializers.Serializer):
    ticket = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="Seconds.")