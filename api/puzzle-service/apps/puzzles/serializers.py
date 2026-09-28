from rest_framework import serializers
from .models import Puzzle, PuzzleAttempt, PuzzleStreak, UserPuzzleRating, DailyPuzzle


class PuzzleSerializer(serializers.ModelSerializer):
    solve_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Puzzle
        fields = [
            "id", "fen", "solution", "rating", "difficulty",
            "themes", "title", "source", "times_played",
            "times_solved", "solve_rate", "created_at",
        ]
        read_only_fields = ["id", "times_played", "times_solved", "created_at"]


class PuzzleAttemptSerializer(serializers.ModelSerializer):
    puzzle_id = serializers.UUIDField(source="puzzle.id", read_only=True)

    class Meta:
        model = PuzzleAttempt
        fields = [
            "id", "puzzle_id", "solved", "attempts_count",
            "hints_used", "time_taken_seconds", "rating_before",
            "rating_after", "rating_change", "created_at",
        ]
        read_only_fields = ["id", "rating_before", "rating_after", "rating_change", "created_at"]


class PuzzleStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuzzleStreak
        fields = [
            "user_id", "current_streak", "longest_streak",
            "last_puzzle_date", "total_solved",
        ]
        read_only_fields = fields


class UserPuzzleRatingSerializer(serializers.ModelSerializer):
    accuracy = serializers.FloatField(read_only=True)

    class Meta:
        model = UserPuzzleRating
        fields = [
            "user_id", "rating", "games_played", "puzzles_solved",
            "puzzles_failed", "accuracy",
        ]
        read_only_fields = fields


class DailyPuzzleSerializer(serializers.ModelSerializer):
    puzzle = PuzzleSerializer(read_only=True)

    class Meta:
        model = DailyPuzzle
        fields = ["id", "date", "puzzle", "created_at"]
        read_only_fields = fields
