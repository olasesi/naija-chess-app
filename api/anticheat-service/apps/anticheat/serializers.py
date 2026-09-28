from rest_framework import serializers

from .models import CheatSignal, GameFlag, UserSanction


class CheatSignalInputSerializer(serializers.Serializer):
    signal_type = serializers.ChoiceField(
        choices=[
            "engine_accuracy",
            "move_time_ms",
            "instant_reply",
            "mouseout_count",
        ]
    )
    game_id = serializers.CharField(max_length=64)
    value = serializers.FloatField()
    opponent_id = serializers.CharField(max_length=255, required=False, default="")
    metadata = serializers.JSONField(required=False, default=dict)


class CheatSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheatSignal
        fields = ["id", "signal_type", "user_id", "game_id", "opponent_id", "value", "metadata", "created_at"]


class GameFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameFlag
        fields = [
            "id",
            "game_id",
            "user_id",
            "opponent_id",
            "suspicion_score",
            "reasons",
            "status",
            "created_at",
            "resolved_at",
            "resolved_by",
        ]
        read_only_fields = ["id", "created_at", "resolved_at", "resolved_by"]

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        from django.utils import timezone

        if instance.status in (GameFlag.Status.REVIEWED, GameFlag.Status.CLEARED, GameFlag.Status.ACTIONED) and not instance.resolved_at:
            request = self.context.get("request")
            instance.resolved_at = timezone.now()
            instance.resolved_by = request.user.id if request else "system"
        if instance.status == GameFlag.Status.OPEN:
            instance.resolved_at = None
            instance.resolved_by = ""
        instance.save(update_fields=["status", "resolved_at", "resolved_by"])
        return instance


class UserSanctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSanction
        fields = [
            "id",
            "user_id",
            "action",
            "reason",
            "related_game_id",
            "applied_by",
            "active",
            "created_at",
        ]
        read_only_fields = ["id", "applied_by", "created_at"]