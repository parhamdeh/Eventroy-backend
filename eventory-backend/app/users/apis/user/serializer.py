"""Serializers for administrator user management."""

from __future__ import annotations

from rest_framework import serializers

from app.users.identifiers import normalize_email, normalize_phone
from app.users.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    """Fields safe to return to an administrator. Never includes password hashes."""

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "username",
            "last_name",
            "email",
            "birth_date",
            "points",
            "is_vip",
            "is_staff",
            "is_superuser",
            "is_active",
            "is_phone_verified",
            "is_email_verified",
            "date_joined",
            "created_at",
        )
        read_only_fields = fields


class AdminCreateSerializer(serializers.Serializer):
    """Input for creating a staff administrator. Superuser cannot be assigned."""

    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    username = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    def validate_phone(self, value: str) -> str:
        return normalize_phone(value)

    def validate_email(self, value: str) -> str:
        if not value:
            return ""
        return normalize_email(value)


class VipUpdateSerializer(serializers.Serializer):
    """Toggle VIP status for a target user."""

    is_vip = serializers.BooleanField()


class AdminUserFilterSerializer(serializers.Serializer):
    """Query parameters for administrator user listing."""

    id = serializers.IntegerField(required=False, min_value=1)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    is_vip = serializers.BooleanField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        if not value:
            return ""
        return normalize_phone(value)

    def validate_email(self, value: str) -> str:
        if not value:
            return ""
        return normalize_email(value)
