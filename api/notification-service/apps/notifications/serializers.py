from rest_framework import serializers
from .models import Notification, PushDevice


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "body", "data", "read_at", "created_at"]
        read_only_fields = ["id", "created_at"]


class MarkReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )


class PushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushDevice
        fields = ["id", "token", "platform", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class InternalSendSerializer(serializers.Serializer):
    recipient_id = serializers.CharField()
    type = serializers.ChoiceField(choices=Notification.Type.choices)
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    data = serializers.JSONField(default=dict, required=False)
