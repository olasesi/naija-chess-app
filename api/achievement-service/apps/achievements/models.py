import uuid

from django.db import models
from django.utils import timezone


class Achievement(models.Model):
    """Static achievement catalog. One row per unlockable achievement."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=48, default="game", db_index=True)
    icon = models.CharField(max_length=16, blank=True, default="🏆")
    xp_reward = models.PositiveIntegerField(default=0)
    # {"event": "game_won", "operator": "gte", "value": 10}
    criteria = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "xp_reward", "code"]

    def __str__(self):
        return f"{self.code}: {self.name}"


class UserAchievement(models.Model):
    """Per-user progress toward and ownership of an achievement."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name="awards")
    progress = models.IntegerField(default=0)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_id", "achievement"], name="uq_user_achievement")
        ]

    def __str__(self):
        return f"{self.user_id}: {self.achievement.code} {self.progress}"


class UserXP(models.Model):
    """Total XP and derived level for a user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    total_xp = models.BigIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id}: level {self.level} ({self.total_xp} xp)"