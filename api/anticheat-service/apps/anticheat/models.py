import uuid

from django.db import models


class CheatSignal(models.Model):
    """A single telemetry observation from a game session."""

    signal_type = models.CharField(max_length=64, db_index=True)

    user_id = models.CharField(max_length=255, db_index=True)
    game_id = models.CharField(max_length=64, db_index=True)
    opponent_id = models.CharField(max_length=255, blank=True, default="")

    value = models.FloatField(default=0.0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["game_id", "signal_type"])]

    def __str__(self):
        return f"{self.signal_type} {self.user_id} {self.game_id}"


class GameFlag(models.Model):
    """A game put on hold for review after crossing the suspicion bar."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REVIEWED = "REVIEWED", "Reviewed"
        CLEARED = "CLEARED", "Cleared"
        ACTIONED = "ACTIONED", "Actioned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_id = models.CharField(max_length=64, unique=True)
    user_id = models.CharField(max_length=255, db_index=True)
    opponent_id = models.CharField(max_length=255, blank=True, default="")
    suspicion_score = models.FloatField(default=0.0)
    reasons = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-suspicion_score", "-created_at"]

    def __str__(self):
        return f"Flag {self.game_id} [{self.status}] {self.suspicion_score:.0f}"


class UserSanction(models.Model):
    """Warning, limitation, or ban applied to a user found cheating."""

    class Action(models.TextChoices):
        WARNING = "WARNING", "Warning"
        LIMITED = "LIMITED", "Limited matchmaking"
        BANNED = "BANNED", "Banned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    action = models.CharField(max_length=16, choices=Action.choices)
    reason = models.TextField(blank=True)
    related_game_id = models.CharField(max_length=64, blank=True, default="")
    applied_by = models.CharField(max_length=255, blank=True, default="")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} {self.action}"