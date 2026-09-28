from django.db import models


class Opening(models.Model):
    eco = models.CharField(max_length=3, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    moves = models.TextField(help_text="Space-separated UCI moves, e.g. 'e2e4 e7e5 g1f3'")
    popularity = models.IntegerField(default=0)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chess_openings"
        ordering = ["eco"]
        verbose_name = "Chess Opening"
        verbose_name_plural = "Chess Openings"

    def __str__(self):
        return f"{self.eco}: {self.name}"
