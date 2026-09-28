import uuid

from django.db import models


class AIGame(models.Model):
    """A persisted human-vs-AI game session."""

    class Color(models.TextChoices):
        WHITE = "w", "White"
        BLACK = "b", "Black"

    class Result(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PLAYER_WIN = "PLAYER_WIN", "Player win"
        AI_WIN = "AI_WIN", "AI win"
        DRAW = "DRAW", "Draw"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    side = models.CharField(max_length=1, choices=Color.choices, default=Color.WHITE)
    level = models.CharField(max_length=16, default="medium")
    fen = models.TextField(default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    moves = models.JSONField(default=list)  # SAN move list
    result = models.CharField(max_length=16, choices=Result.choices, default=Result.PENDING)
    draw_reason = models.CharField(max_length=48, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"AIGame {self.id} ({self.user_id} vs {self.level})"

    @property
    def pgn(self):
        """Export moves as a PGN string with a minimal header."""
        headers = [
            f"[Event \"Computer Chess Game\"]",
            f"[Site \"Chess Platform\"]",
            f"[White \"{'Player' if self.side == 'w' else 'AI'}\"]",
            f"[Black \"{'Player' if self.side == 'b' else 'AI'}\"]",
            f"[Result \"*\"]",
        ]
        body = " ".join(self.moves)
        return "\n".join(headers) + "\n\n" + body