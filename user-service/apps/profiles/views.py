import os
from django.conf import settings
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner, IsAdmin
from .models import UserProfile
from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    AvatarUploadSerializer,
)


class ProfileDetailView(APIView):
    permission_classes = [IsOwner | IsAdmin]

    def get_object(self, userId):
        profile, created = UserProfile.objects.get_or_create(userId=userId)
        return profile

    def get(self, request, userId=None):
        userId = userId or getattr(request.user, "id", None)
        if not userId:
            return Response(
                {"success": False, "message": "User ID required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = self.get_object(userId)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request, userId=None):
        userId = userId or getattr(request.user, "id", None)
        profile = self.get_object(userId)
        self.check_object_permissions(request, profile)

        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(profile).data)


class AvatarUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsOwner]

    def post(self, request):
        userId = getattr(request.user, "id", None)
        profile, _ = UserProfile.objects.get_or_create(userId=userId)
        self.check_object_permissions(request, profile)

        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        avatar = serializer.validated_data["avatar"]

        # Validate file type
        if avatar.content_type not in settings.AVATAR_ALLOWED_TYPES:
            return Response(
                {"success": False, "message": "Only JPEG, PNG, and WebP allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete old avatar
        if profile.avatar:
            old_path = profile.avatar.path
            if os.path.exists(old_path):
                os.remove(old_path)

        profile.avatar = avatar
        profile.save()

        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )


class ProfileSearchView(APIView):
    permission_classes = []  # Any authenticated user

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {"success": False, "message": "Query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profiles = UserProfile.objects.filter(displayName__icontains=query)[:20]
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)
