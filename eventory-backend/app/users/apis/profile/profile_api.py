
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializer import UserProfileSerializer


class UserProfileView(APIView):
    """
    Retrieve or update the authenticated user's profile.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(
        tags=["Profile"],
        summary="Retrieve current user profile",
        responses={200: UserProfileSerializer},
    )
    def get(self, request):
        """Return the authenticated user's profile."""

        serializer = UserProfileSerializer(
            request.user,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Profile"],
        summary="Update current user profile",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    )
    @transaction.atomic
    def patch(self, request):
        """Partially update the authenticated user's profile."""

        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
