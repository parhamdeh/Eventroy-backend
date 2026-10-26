from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import serializers

from app.users.services.date import calculate_age
from app.users.models import User




class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serialize editable profile information for the current user.
    """

    age = serializers.SerializerMethodField()

    class Meta:
        """Define the user profile serialization contract."""

        model = User
        fields = [
            "id",
            "username",
            "last_name",
            "email",
            "phone",
            "profile_photo",
            "birth_date",
            "age",
            "points",
            "created_at",
            "is_vip",
            "is_phone_verified",
            "is_email_verified",
        ]

        read_only_fields = [
            "id",
            "phone",
            "age",
            "points",
            "created_at",
            "is_vip",
            "is_phone_verified",
            "is_email_verified",
        ]

    def get_age(self, obj: User) -> int | None:
        """Return the user's calculated age."""

        return calculate_age(obj.birth_date)

    def validate_birth_date(self, value):
        """Reject birth dates that are in the future."""

        if value is not None and value > timezone.localdate():
            raise serializers.ValidationError(
                _("Birth date cannot be in the future.")
            )

        return value

    def validate_profile_photo(self, value):
        """Validate the uploaded profile image size."""

        if value is not None and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                _("Profile image must not exceed 5 MB.")
            )

        return value
