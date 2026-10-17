"""Permission classes for user administration endpoints."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsSuperUser(BasePermission):
    """Only Django superusers may create other administrators."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_superuser)


class IsStaffUser(BasePermission):
    """Active staff users may list users and manage VIP status."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_staff)
