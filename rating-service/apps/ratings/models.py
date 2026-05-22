from django.db import models


class TimeControl(models.TextChoices):
    BULLET = "bullet", "Bullet"
    BLITZ = "blitz", "Blitz"
    RAPID = "rapid", "Rapid"
    CLASSICAL = "classical", "Classical"
    PUZZLE = "puzzle", "Puzzle"


class PlayerRating(models.Model):
    userId = models.CharField(max_length=36, db_index=True)
    timeControl = models.CharField(max_length=10, choices=TimeControl.choices)
    rating = models.FloatField(default=1500.0)
    ratingDeviation = models.FloatField(default=350.0)
    volatility = models.FloatField(default=0.06)
    gamesPlayed = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    provisional = models.BooleanField(default=True)
    lastGameAt = models.DateTimeField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "player_ratings"
        unique_together = [("userId", "timeControl")]
        indexes = [
            models.Index(fields=["timeControl", "-rating"]),
            models.Index(fields=["userId", "timeControl"]),
        ]
        verbose_name = "Player Rating"
        verbose_name_plural = "Player Ratings"

    def __str__(self):
        return f"{self.userId} [{self.timeControl}] r={self.rating:.0f} RD={self.ratingDeviation:.0f}"


class RatingHistory(models.Model):
    userId = models.CharField(max_length=36, db_index=True)
    timeControl = models.CharField(max_length=10, choices=TimeControl.choices)
    rating = models.FloatField()
    ratingDeviation = models.FloatField()
    volatility = models.FloatField()
    gameId = models.CharField(max_length=36, db_index=True, null=True, blank=True)
    opponentId = models.CharField(max_length=36, null=True, blank=True)
    result = models.CharField(max_length=5, null=True, blank=True)
    recordedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rating_history"
        indexes = [
            models.Index(fields=["userId", "timeControl", "-recordedAt"]),
        ]
        ordering = ["-recordedAt"]
        verbose_name = "Rating History"
        verbose_name_plural = "Rating Histories"

    def __str__(self):
        return f"{self.userId} [{self.timeControl}] {self.rating:.0f} @ {self.recordedAt}"
