import uuid
from django.db import models


class Tournament(models.Model):
    class Type(models.TextChoices):
        SWISS = "SWISS", "Swiss"
        ROUND_ROBIN = "ROUND_ROBIN", "Round Robin"
        KNOCKOUT = "KNOCKOUT", "Knockout"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SWISS)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    time_control_initial = models.IntegerField(default=600)
    time_control_increment = models.IntegerField(default=5)
    rating_min = models.IntegerField(null=True, blank=True)
    rating_max = models.IntegerField(null=True, blank=True)
    max_players = models.IntegerField(default=64)
    min_players = models.IntegerField(default=4)
    total_rounds = models.IntegerField(default=7)
    current_round = models.IntegerField(default=0)
    creator_id = models.CharField(max_length=255)
    allow_bye = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tournaments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.type}, {self.status})"


class TournamentPlayer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, related_name="players", on_delete=models.CASCADE)
    user_id = models.CharField(max_length=255)
    seed = models.IntegerField(default=0)
    score = models.FloatField(default=0.0)
    tiebreak1 = models.FloatField(default=0.0)
    tiebreak2 = models.FloatField(default=0.0)
    has_bye = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tournament_players"
        unique_together = [("tournament", "user_id")]
        ordering = ["-score", "-tiebreak1", "-tiebreak2"]

    def __str__(self):
        return f"{self.user_id} in {self.tournament_id}"


class TournamentRound(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, related_name="rounds", on_delete=models.CASCADE)
    round_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tournament_rounds"
        unique_together = [("tournament", "round_number")]
        ordering = ["round_number"]

    def __str__(self):
        return f"Round {self.round_number} of {self.tournament_id}"


class TournamentMatch(models.Model):
    class Result(models.TextChoices):
        WHITE_WIN = "1-0", "White Win"
        BLACK_WIN = "0-1", "Black Win"
        DRAW = "1/2-1/2", "Draw"
        BYE = "BYE", "Bye"
        NOT_PLAYED = "*", "Not Played"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, related_name="matches", on_delete=models.CASCADE)
    round = models.ForeignKey(TournamentRound, related_name="matches", on_delete=models.CASCADE)
    white_player = models.ForeignKey(TournamentPlayer, related_name="white_matches", on_delete=models.CASCADE, null=True, blank=True)
    black_player = models.ForeignKey(TournamentPlayer, related_name="black_matches", on_delete=models.CASCADE, null=True, blank=True)
    game_id = models.CharField(max_length=255, null=True, blank=True)
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.NOT_PLAYED)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    board_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tournament_matches"
        ordering = ["board_number"]
        indexes = [
            models.Index(fields=["tournament", "status"]),
        ]

    def __str__(self):
        return f"Match {self.id} R{self.round.round_number}"
