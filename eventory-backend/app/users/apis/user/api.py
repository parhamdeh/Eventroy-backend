"""Administrator user listing, creation, and VIP management."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.api.mixins import ApiAuthMixin
from app.api.pagination import LimitOffsetPagination, get_paginated_response
from app.api.throttle import AdminRequestThrottle
from app.users.apis.user.serializer import (
    AdminCreateSerializer,
    AdminUserFilterSerializer,
    AdminUserSerializer,
    VipUpdateSerializer,
)
from app.users.permissions import IsStaffUser, IsSuperUser
from app.users.selectors.users import user_get_by_id, user_list
from app.users.services.users import create_superuser, set_user_vip
from app.core.exceptions import NotFoundError
from django.utils.translation import gettext as _


class ListCreateAdminView(ApiAuthMixin, APIView):
    """
    GET: paginated user listing for staff.
    POST: create a staff administrator (superuser-only).
    """

    throttle_classes = (AdminRequestThrottle,)

    def get_permissions(self):  
        if self.request.method == "POST":
            return [IsSuperUser()]
        return [IsStaffUser()]

    @extend_schema(
        tags=["admin"],
        parameters=[AdminUserFilterSerializer],
        responses={200: AdminUserSerializer(many=True)},
        description="Paginated user listing with exact filters on id, phone, email, and VIP.",
    )
    def get(self, request: Request) -> Response:
        # add search and filter for users
        # need to refactor!
        filters = AdminUserFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        data = filters.validated_data
        queryset = user_list(
            user_id=data.get("id"),
            phone=data.get("phone") or None,
            email=data.get("email") or None,
            is_vip=data.get("is_vip"),
        )
        return get_paginated_response(
            pagination_class=LimitOffsetPagination,
            serializer_class=AdminUserSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )

    @extend_schema(
        tags=["admin"],
        request=AdminCreateSerializer,
        responses={201: AdminUserSerializer},
        description="Create a staff administrator. Superuser and VIP cannot be granted.",
    )
    def post(self, request: Request) -> Response:
        serializer = AdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_superuser(data=serializer.validated_data)
        return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(ApiAuthMixin, APIView):
    """Retrieve a single user for staff administrators."""

    throttle_classes = (AdminRequestThrottle,)
    permission_classes = (IsStaffUser,)

    @extend_schema(tags=["admin"], responses={200: AdminUserSerializer})
    def get(self, request: Request, user_id: int) -> Response:
        user = user_get_by_id(user_id=user_id)
        if user is None:
            raise NotFoundError(_("User not found."))
        return Response(AdminUserSerializer(user).data)


class AdminUserVipView(ApiAuthMixin, APIView):
    """Change VIP status. Ordinary users cannot call this endpoint."""

    throttle_classes = (AdminRequestThrottle,)
    permission_classes = (IsStaffUser,)

    @extend_schema(
        tags=["admin"],
        request=VipUpdateSerializer,
        responses={200: AdminUserSerializer},
        description="Set is_vip for a target user. Public profile APIs never accept this field.",
    )
    def patch(self, request: Request, user_id: int) -> Response:
        serializer = VipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = set_user_vip(user_id=user_id, is_vip=serializer.validated_data["is_vip"])
        return Response(AdminUserSerializer(user).data)
