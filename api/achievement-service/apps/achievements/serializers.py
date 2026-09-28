from rest_framework import serializers

from .models import Achievement, UserAchievement, UserXP
from .engine import xp_bounds


class AchievementSerializer(serializers.ModelSerializer):
    unlocked = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    progress_target = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = [
            "id",
            "code",
            "name",
            "description",
            "category",
            "icon",
            "xp_reward",
            "criteria",
            "unlocked",
            "progress",
            "progress_target",
        ]

    def _user_progress(self, obj):
        user = self.context["request"].user
        ua = UserAchievement.objects.filter(user_id=user.id, achievement=obj).first()
        return ua

    def get_unlocked(self, obj):
        ua = self._user_progress(obj)
        return ua.unlocked_at is not None if ua else False

    def get_progress(self, obj):
        ua = self._user_progress(obj)
        return ua.progress if ua else 0

    def get_progress_target(self, obj):
        return obj.criteria.get("value", 1) if obj.criteria else 1


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ["id", "achievement", "progress", "unlocked_at", "updated_at"]


class UserXPSerializer(serializers.ModelSerializer):
    level_progress = serializers.SerializerMethodField()
    level_floor = serializers.SerializerMethodField()
    level_top = serializers.SerializerMethodField()
    next_level_at = serializers.SerializerMethodField()

    class Meta:
        model = UserXP
        fields = [
            "id",
            "user_id",
            "total_xp",
            "level",
            "level_floor",
            "level_top",
            "level_progress",
            "next_level_at",
            "updated_at",
        ]

    def get_level_floor(self, obj):
        floor, _ = xp_bounds(obj.level)
        return floor

    def get_level_top(self, obj):
        _, top = xp_bounds(obj.level)
        return top

    def get_level_progress(self, obj):
        floor, top = xp_bounds(obj.level)
        span = top - floor
        return round((obj.total_xp - floor) / span * 100, 1) if span else 100.0

    def get_next_level_at(self, obj):
        _, top = xp_bounds(obj.level)
        return top


class EventInputSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=64)
    value = serializers.IntegerField(default=1, min_value=1)