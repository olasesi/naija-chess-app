from rest_framework import serializers

from .models import UserBlock


class UserBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBlock
        fields = ["id", "userId", "blockedId", "type", "reason", "createdAt", "updatedAt"]
        read_only_fields = ["id", "createdAt", "updatedAt"]


class UserBlockCreateSerializer(serializers.Serializer):
    blockedId = serializers.UUIDField()
    type = serializers.ChoiceField(choices=["BLOCK", "MUTE"])
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True)