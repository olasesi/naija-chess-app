from django.db import models


class UserStats(models.Model):
    userId = models.CharField(max_length=36, unique=True, db_index=True)
    gamesPlayed = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    winStreak = models.IntegerField(default=0)
    bestWinStreak = models.IntegerField(default=0)
    bulletRating = models.IntegerField(default=1200)
    blitzRating = models.IntegerField(default=1200)
    rapidRating = models.IntegerField(default=1200)
    classicalRating = models.IntegerField(default=1200)
    puzzleRating = models.IntegerField(default=1200)
    puzzleRatingMax = models.IntegerField(default=1200)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_stats"
        verbose_name = "User Stats"
        verbose_name_plural = "User Stats"

    def __str__(self):
        return f"Stats[{self.userId}]"
