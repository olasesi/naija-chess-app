import random

from django.db.models import Avg, F
from django.db.models.functions import Abs
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .engine import PuzzleRating, select_puzzle_rating, update_puzzle_rating
from .models import (
    DailyPuzzle,
    Puzzle,
    PuzzleAttempt,
    PuzzleStreak,
    UserPuzzleRating,
)
from .serializers import (
    DailyPuzzleSerializer,
    PuzzleAttemptSerializer,
    PuzzleSerializer,
    PuzzleStreakSerializer,
    UserPuzzleRatingSerializer,
)


class PuzzleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Puzzles:
    - GET  /api/puzzles/            - list puzzles
    - GET  /api/puzzles/:id/        - puzzle detail
    - GET  /api/puzzles/next/       - get next puzzle for current user
    - POST /api/puzzles/attempt/    - submit an attempt
    - GET  /api/puzzles/streak/     - user's current streak
    - GET  /api/puzzles/rating/     - user's puzzle rating
    - GET  /api/puzzles/daily/      - puzzle of the day
    - GET  /api/puzzles/history/    - user's attempt history
    - GET  /api/puzzles/stats/      - aggregate stats for a puzzle
    """
    queryset = Puzzle.objects.filter(status="ACTIVE")
    serializer_class = PuzzleSerializer
    filterset_fields = ["difficulty", "rating"]

    def get_queryset(self):
        qs = super().get_queryset()
        difficulty = self.request.query_params.get("difficulty")
        min_rating = self.request.query_params.get("min_rating")
        max_rating = self.request.query_params.get("max_rating")
        theme = self.request.query_params.get("theme")

        if difficulty:
            qs = qs.filter(difficulty=difficulty.upper())
        if min_rating:
            qs = qs.filter(rating__gte=int(min_rating))
        if max_rating:
            qs = qs.filter(rating__lte=int(max_rating))
        if theme:
            qs = qs.filter(themes__icontains=theme)  # JSON field contains
        return qs

    def _get_or_create_rating(self, user_id):
        obj, _ = UserPuzzleRating.objects.get_or_create(user_id=user_id)
        return obj

    def _to_engine(self, obj: UserPuzzleRating) -> PuzzleRating:
        return PuzzleRating(
            rating=obj.rating,
            rd=350.0 if obj.games_played < 3 else 60.0,
            volatility=0.06,
            games=obj.games_played,
        )

    @action(detail=False, methods=["GET"])
    def next(self, request):
        """Get the next puzzle for the current user, matched to their rating."""
        user_id = request.user.id
        rating_obj = self._get_or_create_rating(user_id)
        engine = self._to_engine(rating_obj)
        target = select_puzzle_rating(engine, is_beginner=engine.games < 5)

        # Prefer puzzles near the user's level, avoiding ones just attempted
        recent_ids = list(
            PuzzleAttempt.objects.filter(user_id=user_id)
            .order_by("-created_at")
            .values_list("puzzle_id", flat=True)[:20]
        )

        candidates = Puzzle.objects.filter(status="ACTIVE").exclude(id__in=recent_ids)
        # ±250 rating window
        candidates = candidates.filter(rating__gte=target - 250, rating__lte=target + 250)
        if not candidates.exists():
            candidates = Puzzle.objects.filter(status="ACTIVE").exclude(id__in=recent_ids)
        if not candidates.exists():
            candidates = Puzzle.objects.filter(status="ACTIVE")

        # Pick randomly among the 10 closest to the target rating
        closest = list(candidates.order_by(Abs(F("rating") - target))[:10])
        puzzle = random.choice(closest) if closest else candidates.first()

        if not puzzle:
            return Response({"detail": "No puzzles available"}, status=status.HTTP_404_NOT_FOUND)

        return Response(PuzzleSerializer(puzzle).data)

    @action(detail=False, methods=["POST"])
    def attempt(self, request):
        """
        Submit a puzzle attempt. Body: { puzzle_id, solved, time_taken_seconds, hints_used }
        Updates puzzle rating and streak.
        """
        user_id = request.user.id
        puzzle_id = request.data.get("puzzle_id")
        solved = request.data.get("solved", False)
        time_taken = int(request.data.get("time_taken_seconds", 0))
        hints_used = int(request.data.get("hints_used", 0))

        try:
            puzzle = Puzzle.objects.get(id=puzzle_id, status="ACTIVE")
        except (Puzzle.DoesNotExist, ValueError):
            return Response({"detail": "Puzzle not found"}, status=status.HTTP_404_NOT_FOUND)

        # get current rating
        rating_obj = self._get_or_create_rating(user_id)
        engine = self._to_engine(rating_obj)
        rating_before = engine.rating

        new_engine = update_puzzle_rating(
            engine,
            puzzle.rating,
            solved=solved,
            time_taken_seconds=time_taken,
            hints_used=hints_used,
        )
        rating_change = new_engine.rating - rating_before

        # persist attempt
        attempt = PuzzleAttempt.objects.create(
            user_id=user_id,
            puzzle=puzzle,
            solved=solved,
            time_taken_seconds=time_taken,
            hints_used=hints_used,
            rating_before=rating_before,
            rating_after=new_engine.rating,
            rating_change=rating_change,
        )

        # update aggregate counters
        Puzzle.objects.filter(id=puzzle.id).update(times_played=F("times_played") + 1)
        if solved:
            Puzzle.objects.filter(id=puzzle.id).update(times_solved=F("times_solved") + 1)

        # update user rating record
        rating_obj.rating = new_engine.rating
        rating_obj.games_played += 1
        if solved:
            rating_obj.puzzles_solved += 1
        else:
            rating_obj.puzzles_failed += 1
        rating_obj.save()

        # update streak (only for daily puzzles)
        today = timezone.now().date()
        daily = DailyPuzzle.objects.filter(date=today).first()
        if daily and daily.puzzle_id == puzzle.id and solved:
            streak, _ = PuzzleStreak.objects.get_or_create(user_id=user_id)
            streak.update_streak(today)

        return Response(
            {
                "attempt": PuzzleAttemptSerializer(attempt).data,
                "rating_before": rating_before,
                "rating_after": new_engine.rating,
                "rating_change": rating_change,
                "accuracy": rating_obj.accuracy,
            }
        )

    @action(detail=False, methods=["GET"])
    def streak(self, request):
        """User's current puzzle streak"""
        user_id = request.user.id
        streak, _ = PuzzleStreak.objects.get_or_create(user_id=user_id)
        return Response(PuzzleStreakSerializer(streak).data)

    @action(detail=False, methods=["GET"])
    def rating(self, request):
        """User's puzzle rating"""
        user_id = request.user.id
        rating_obj = self._get_or_create_rating(user_id)
        return Response(UserPuzzleRatingSerializer(rating_obj).data)

    @action(detail=False, methods=["GET"])
    def daily(self, request):
        """Puzzle of the day (falls back to a random puzzle if not set)"""
        today = timezone.now().date()
        daily = DailyPuzzle.objects.filter(date=today).select_related("puzzle").first()
        if not daily:
            # fallback: pick a random medium puzzle
            puzzle = Puzzle.objects.filter(status="ACTIVE", difficulty="MEDIUM").first()
            if not puzzle:
                return Response({"detail": "No daily puzzle available"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"date": today, "puzzle": PuzzleSerializer(puzzle).data})
        return Response(DailyPuzzleSerializer(daily).data)

    @action(detail=False, methods=["GET"])
    def history(self, request):
        """User's puzzle attempt history (paginated)"""
        user_id = request.user.id
        attempts = PuzzleAttempt.objects.filter(user_id=user_id).select_related("puzzle")
        page = self.paginate_queryset(attempts)
        if page is not None:
            serializer = PuzzleAttemptSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(PuzzleAttemptSerializer(attempts, many=True).data)

    @action(detail=True, methods=["GET"])
    def stats(self, request, pk=None):
        """Aggregate solve stats for a specific puzzle"""
        puzzle = self.get_object()
        total = PuzzleAttempt.objects.filter(puzzle=puzzle).count()
        solved = PuzzleAttempt.objects.filter(puzzle=puzzle, solved=True).count()
        avg_time = (
            PuzzleAttempt.objects.filter(puzzle=puzzle, solved=True)
            .aggregate(avg=Avg("time_taken_seconds"))
            .get("avg") or 0
        )
        return Response(
            {
                "puzzle_id": str(puzzle.id),
                "total_attempts": total,
                "solved_count": solved,
                "solve_rate": puzzle.solve_rate,
                "avg_solve_time_seconds": round(avg_time) if avg_time else 0,
            }
        )
