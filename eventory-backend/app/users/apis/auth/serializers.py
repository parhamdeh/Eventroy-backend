"""Request and response serializers for authentication endpoints."""

from __future__ import annotations

from rest_framework import serializers

from app.users.identifiers import normalize_email, normalize_phone
from app.users.models import User

CHANNEL_CHOICES = (("phone", "phone"), ("email", "email"))


class UserPublicSerializer(serializers.ModelSerializer):
    """Safe user representation returned after authentication."""

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
            "is_phone_verified",
            "is_email_verified",
            "date_joined",
        )
        read_only_fields = fields


class SignUpSerializer(serializers.Serializer):
    """Registration payload. Privileged fields are not writable."""

    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    username = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    birth_date = serializers.DateField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        return normalize_phone(value)

    def validate_email(self, value: str) -> str:
        if not value:
            return ""
        return normalize_email(value)

    def validate(self, attrs: dict) -> dict:
        if attrs["channel"] == "email" and not attrs.get("email"):
            raise serializers.ValidationError({"email": "This field is required."})
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    """OTP confirmation for signup."""

    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    identifier = serializers.CharField(max_length=254)
    otp = serializers.CharField(min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    """Password login using phone or email."""

    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    identifier = serializers.CharField(max_length=254)
    password = serializers.CharField(write_only=True, max_length=128)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password-reset OTP on a verified identifier."""

    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    identifier = serializers.CharField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm a password-reset OTP and set a new password."""

    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES)
    identifier = serializers.CharField(max_length=254)
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128)


class TokenRefreshRequestSerializer(serializers.Serializer):
    """Refresh-token rotation request."""

    refresh = serializers.CharField()


class GoogleAuthSerializer(serializers.Serializer):
    """Google ID token submitted by the frontend."""

    id_token = serializers.CharField()


class AuthTokenResponseSerializer(serializers.Serializer):
    """Access/refresh pair plus public user data."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserPublicSerializer()


class PendingOtpResponseSerializer(serializers.Serializer):
    """Signup / OTP-issued acknowledgement."""

    channel = serializers.CharField()
    identifier = serializers.CharField()
    expires_in = serializers.IntegerField()
