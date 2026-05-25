from django.db import models


class AnalysisStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ANALYZING = "ANALYZING", "Analyzing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class AnalysisDepth(models.TextChoices):
    QUICK = "quick", "Quick"
    NORMAL = "normal", "Normal"
    DEEP = "deep", "Deep"


class GameAnalysis(models.Model):
    gameId = models.CharField(max_length=36, unique=True, db_index=True)
    pgn = models.TextField()
    fen = models.CharField(max_length=128)
    status = models.CharField(max_length=10, choices=AnalysisStatus.choices, default=AnalysisStatus.PENDING, db_index=True)
    depth = models.CharField(max_length=10, choices=AnalysisDepth.choices, default=AnalysisDepth.NORMAL)
    totalMoves = models.IntegerField(default=0)
    analyzedMoves = models.IntegerField(default=0)
    accuracy = models.JSONField(default=dict)
    averageCentipawnLoss = models.JSONField(default=dict)
    classifications = models.JSONField(default=dict)
    moves = models.JSONField(default=list)
    eco = models.CharField(max_length=3, blank=True)
    opening = models.CharField(max_length=200, blank=True)
    error = models.TextField(blank=True)
    requestedBy = models.CharField(max_length=36)
    createdAt = models.DateTimeField(auto_now_add=True)
    completedAt = models.DateTimeField(null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_analysis"
        ordering = ["-createdAt"]
        indexes = [
            models.Index(fields=["status", "createdAt"]),
            models.Index(fields=["requestedBy", "-createdAt"]),
        ]

    def __str__(self):
        return f"Analysis[{self.gameId}] ({self.status})"


class CachedPosition(models.Model):
    fen = models.CharField(max_length=128, unique=True, db_index=True)
    depth = models.IntegerField()
    score = models.IntegerField()
    mate = models.IntegerField(null=True, blank=True)
    bestMove = models.CharField(max_length=10)
    continuation = models.JSONField(default=list)
    nodesSearched = models.BigIntegerField(default=0)
    timeMs = models.IntegerField(default=0)
    evaluatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cached_positions"
        indexes = [models.Index(fields=["-depth"])]

    def __str__(self):
        return f"Pos[{self.fen[:30]}...] @ d={self.depth}"
