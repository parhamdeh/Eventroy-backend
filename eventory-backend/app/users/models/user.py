
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the application.

    Authentication:
        Users authenticate using their unique phone number.

    Personal information:
        Username and last name are required.
        Email, profile photo, and birth date are optional.

    Permissions:
        Django's PermissionsMixin provides group membership,
        user permissions, and superuser permission support.

    Points:
        Integer score constrained to the inclusive range [0, 5].

    Security:
        Password hashing and password verification are handled by
        Django's AbstractBaseUser implementation.
    """

    phone = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name=_("Phone number"),
        help_text=_("Required unique phone number used for authentication."),
    )

    username = models.CharField(
        max_length=150,
        verbose_name=_("Name"),
        help_text=_("Required display name. It does not need to be unique."),
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name=_("Last name"),
        help_text=_("Required family name of the user."),
    )

    email = models.EmailField(
        blank=True,
        default="",
        verbose_name=_("Email address"),
        help_text=_("Optional email address. Non-empty email addresses must be unique."),
    )

    profile_photo = models.ImageField(
        upload_to="users/profile_photos/",
        blank=True,
        default="",
        verbose_name=_("Profile photo"),
        help_text=_("Optional profile picture."),
    )

    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date of birth"),
        help_text=_("Optional date of birth."),
    )

    points = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5),
        ],
        verbose_name=_("Points"),
        help_text=_("User score. Must be an integer between 0 and 5."),
    )

    is_vip = models.BooleanField(
        default=False,
        verbose_name=_("VIP status"),
        help_text=_("Whether this user has VIP membership."),
    )

    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name=_("Phone verified"),
        help_text=_("Whether the phone number has been verified via OTP."),
    )

    is_email_verified = models.BooleanField(
        default=False,
        verbose_name=_("Email verified"),
        help_text=_("Whether the email address has been verified via OTP or Google."),
    )

    google_sub = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Google subject"),
        help_text=_("Stable Google account identifier (sub). Empty when unused."),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this account is allowed to authenticate."),
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("Staff status"),
        help_text=_("Whether this user can access the Django admin site."),
    )

    date_joined = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name=_("Date joined"),
        help_text=_("Date and time when the account was created."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("Timestamp when this record was created."),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
        help_text=_("Timestamp of the last model save."),
    )

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username", "last_name"]

    class Meta:
        """Database constraints and default presentation for users."""

        ordering = ("-created_at",)

        verbose_name = _("User")
        verbose_name_plural = _("Users")

        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~Q(email=""),
                name="users_user_email_ci_uniq",
            ),
            models.UniqueConstraint(
                "google_sub",
                condition=~Q(google_sub=""),
                name="users_user_google_sub_uniq",
            ),
            models.CheckConstraint(
                condition=Q(points__gte=0) & Q(points__lte=5),
                name="users_user_points_0_5",
            ),
        ]

        indexes = [
            models.Index(
                fields=["-created_at"],
                name="users_user_created_idx",
            ),
            models.Index(
                fields=["is_active", "is_staff"],
                name="users_user_status_idx",
            ),
            models.Index(
                fields=["is_vip"],
                name="users_user_is_vip_idx",
            ),
        ]

    def __str__(self) -> str:
        """Return a concise human-readable representation of the user."""
        return f"{self.phone} ({self.username})"

    def save(self, *args, **kwargs):
        """
        Normalize phone and email values before saving.

        Email is normalized to lowercase so that the case-insensitive
        unique database constraint behaves consistently for normal writes.
        """
        if self.phone:
            self.phone = self.phone.strip()

        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = ""

        return super().save(*args, **kwargs)
