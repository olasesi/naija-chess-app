from django.db import models


class TimeControl(models.TextChoices):
    BULLET = "bullet", "Bullet"
    BLITZ = "blitz", "Blitz"
    RAPID = "rapid", "Rapid"
    CLASSICAL = "classical", "Classical"
    PUZZLE = "puzzle", "Puzzle"


class CachedLeaderboard(models.Model):
    timeControl = models.CharField(max_length=10, choices=TimeControl.choices, unique=True)
    rankings = models.JSONField(default=list)
    totalPlayers = models.IntegerField(default=0)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cached_leaderboards"
        verbose_name = "Cached Leaderboard"
        verbose_name_plural = "Cached Leaderboards"

    def __str__(self):
        return f"Leaderboard [{self.timeControl}] — {self.totalPlayers} players"
