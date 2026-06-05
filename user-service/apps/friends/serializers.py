from rest_framework import serializers
from .models import Friend, FriendStatus


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friend
        fields = ["id", "userId", "friendId", "status", "createdAt", "updatedAt"]
        read_only_fields = ["id", "createdAt", "updatedAt"]


class FriendRequestSerializer(serializers.Serializer):
    friendId = serializers.UUIDField()


class FriendActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["accept", "decline", "block"])
