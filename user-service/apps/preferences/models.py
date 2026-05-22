from django.db import models


class UserPreference(models.Model):
    userId = models.CharField(max_length=36, unique=True, db_index=True)
    theme = models.CharField(max_length=20, default="dark")
    boardStyle = models.CharField(max_length=20, default="classic")
    pieceStyle = models.CharField(max_length=20, default="standard")
    soundEnabled = models.BooleanField(default=True)
    showAnalysis = models.BooleanField(default=True)
    autoPromote = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preferences"
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Prefs[{self.userId}]"
