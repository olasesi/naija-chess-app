from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "userId", "displayName", "bio", "avatar",
            "country", "title", "createdAt", "updatedAt",
        ]
        read_only_fields = ["userId", "createdAt", "updatedAt"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["displayName", "bio", "country", "title"]
        extra_kwargs = {
            "displayName": {"required": False, "min_length": 2, "max_length": 30},
            "bio": {"required": False, "max_length": 500},
            "country": {"required": False, "min_length": 2, "max_length": 2},
            "title": {"required": False, "max_length": 10},
        }


class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()
