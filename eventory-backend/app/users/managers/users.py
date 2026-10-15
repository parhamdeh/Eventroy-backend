
from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom manager responsible for creating regular users and superusers.

    Phone number is the unique authentication identifier. User passwords
    are always processed through Django's password-hashing mechanism.

    This manager provides the standard creation methods expected by
    Django's authentication system and the createsuperuser command.
    """

    use_in_migrations = True

    def create_user(
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ):
        """
        Create and persist a regular user.

        Args:
            phone: Unique phone number used for authentication.
            password: Raw password to hash, or None for an unusable password.
            **extra_fields: Additional model fields such as username,
                last_name, email, and birth_date.

        Returns:
            The newly created user instance.

        Raises:
            ValueError: If the phone number or required names are missing.
        """
        if not phone or not phone.strip():
            raise ValueError(_("A phone number must be provided."))

        username = extra_fields.get("username")
        last_name = extra_fields.get("last_name")

        if not isinstance(username, str) or not username.strip():
            raise ValueError(_("A username must be provided."))

        if not isinstance(last_name, str) or not last_name.strip():
            raise ValueError(_("A last name must be provided."))

        phone = phone.strip()
        extra_fields["username"] = username.strip()
        extra_fields["last_name"] = last_name.strip()

        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email).strip().lower()
        else:
            extra_fields["email"] = ""

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        phone: str,
        password: str | None = None,
        **extra_fields: Any,
    ):
        """
        Create and persist a superuser with administrative privileges.

        Args:
            phone: Unique phone number used for authentication.
            password: Raw password to hash.
            **extra_fields: Additional user fields.

        Returns:
            The newly created superuser.

        Raises:
            ValueError: If the required administrative flags are invalid.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("A superuser must have is_staff=True."))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("A superuser must have is_superuser=True."))

        if extra_fields.get("is_active") is not True:
            raise ValueError(_("A superuser must have is_active=True."))

        if not password:
            raise ValueError(_("A password must be provided for a superuser."))

        return self.create_user(
            phone=phone,
            password=password,
            **extra_fields,
        )
