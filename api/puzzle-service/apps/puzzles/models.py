from django.db import models
import uuid


class Puzzle(models.Model):
    """A tactical chess puzzle (mate-in-N, fork, pin, etc.)"""
    DIFFICULTY_CHOICES = [
        ("EASY", "Easy"),
        ("MEDIUM", "Medium"),
        ("HARD", "Hard"),
        ("EXPERT", "Expert"),
    ]
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("ARCHIVED", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fen = models.CharField(max_length=100, help_text="Position before the puzzle move")
    solution = models.JSONField(help_text="List of moves [{'from':'e4','to':'e5'}, ...]")
    rating = models.IntegerField(default=1200, help_text="Puzzle difficulty rating")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="MEDIUM")
    themes = models.JSONField(default=list, blank=True, help_text="List of theme tags e.g. ['fork','pin']")
    title = models.CharField(max_length=200, blank=True, default="")
    source = models.CharField(max_length=200, blank=True, default="", help_text="Origin/source game")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    times_played = models.PositiveIntegerField(default=0)
    times_solved = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-rating"]
        indexes = [
            models.Index(fields=["status", "rating"]),
            models.Index(fields=["difficulty"]),
        ]

    def __str__(self):
        return f"Puzzle {self.id} ({self.difficulty}, {self.rating})"

    @property
    def solve_rate(self):
        if self.times_played == 0:
            return 0.0
        return round(self.times_solved / self.times_played * 100, 1)


class PuzzleAttempt(models.Model):
    """One user's attempt at solving a puzzle"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE, related_name="attempts")
    solved = models.BooleanField(default=False)
    attempts_count = models.PositiveIntegerField(default=1)
    hints_used = models.PositiveIntegerField(default=0)
    time_taken_seconds = models.PositiveIntegerField(default=0)
    rating_before = models.IntegerField(null=True, blank=True)
    rating_after = models.IntegerField(null=True, blank=True)
    rating_change = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id", "puzzle"]),
        ]

    def __str__(self):
        return f"{self.user_id} on {self.puzzle_id} ({'solved' if self.solved else 'failed'})"


class PuzzleStreak(models.Model):
    """Per-user daily puzzle streak"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, unique=True)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_puzzle_date = models.DateField(null=True, blank=True)
    total_solved = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id}: {self.current_streak} day streak"

    def update_streak(self, puzzle_date):
        """Update streak given the date of a completed puzzle"""
        if self.last_puzzle_date is None:
            self.current_streak = 1
        else:
            from datetime import timedelta
            delta = puzzle_date - self.last_puzzle_date
            if delta.days == 0:
                return  # already counted today
            elif delta.days == 1:
                self.current_streak += 1
            else:
                self.current_streak = 1
        self.last_puzzle_date = puzzle_date
        self.total_solved += 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()


class UserPuzzleRating(models.Model):
    """Glicko-like puzzle rating per user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, unique=True)
    rating = models.IntegerField(default=1200)
    games_played = models.PositiveIntegerField(default=0)
    puzzles_solved = models.PositiveIntegerField(default=0)
    puzzles_failed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id}: {self.rating}"

    @property
    def accuracy(self):
        total = self.puzzles_solved + self.puzzles_failed
        if total == 0:
            return 0.0
        return round(self.puzzles_solved / total * 100, 1)


class DailyPuzzle(models.Model):
    """Puzzle of the day - one per calendar date"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    puzzle = models.ForeignKey(Puzzle, on_delete=models.PROTECT, related_name="daily_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Daily puzzle {self.date}"
