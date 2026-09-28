import pytest
from datetime import date, timedelta

from puzzles.models import (
    Puzzle,
    PuzzleAttempt,
    PuzzleStreak,
    UserPuzzleRating,
    DailyPuzzle,
)
from puzzles.engine import (
    PuzzleRating,
    update_puzzle_rating,
    select_puzzle_rating,
    expected_score,
)


# ─────────────────────────────────────────────────────────────
# Unit tests: rating engine (no DB)
# ─────────────────────────────────────────────────────────────
class TestRatingEngine:
    def test_expected_score_symmetric(self):
        """Two equal ratings should expect 0.5"""
        score = expected_score(1200, 1200)
        assert abs(score - 0.5) < 0.001

    def test_expected_score_underdog(self):
        """Lower-rated player expects < 0.5"""
        score = expected_score(1000, 1600)
        assert score < 0.5

    def test_expected_score_favorite(self):
        """Higher-rated player expects > 0.5"""
        score = expected_score(1600, 1000)
        assert score > 0.5

    def test_solving_gains_rating(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=5)
        new = update_puzzle_rating(user, 1200, solved=True)
        assert new.rating > 1200
        assert new.games == 6

    def test_failing_loses_rating(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=5)
        new = update_puzzle_rating(user, 1200, solved=False)
        assert new.rating < 1200

    def test_fast_solve_gains_more_than_slow(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=5)
        fast = update_puzzle_rating(user, 1200, True, time_taken_seconds=10, max_time_seconds=120)
        slow = update_puzzle_rating(user, 1200, True, time_taken_seconds=600, max_time_seconds=120)
        assert fast.rating > slow.rating

    def test_hints_reduce_gain(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=5)
        clean = update_puzzle_rating(user, 1200, True, hints_used=0)
        hinted = update_puzzle_rating(user, 1200, True, hints_used=3)
        assert clean.rating > hinted.rating

    def test_beating_harder_puzzle_gains_more(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=5)
        easy = update_puzzle_rating(user, 1000, True)
        hard = update_puzzle_rating(user, 1800, True)
        assert hard.rating > easy.rating

    def test_uncertainty_shrinks_with_games(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=1)
        new = update_puzzle_rating(user, 1200, True)
        assert new.rd < 350.0

    def test_beginner_gets_easier_puzzles(self):
        novice = PuzzleRating(rating=1600, rd=350.0, games=0)
        target = select_puzzle_rating(novice, is_beginner=True)
        assert target < 1600
        assert target <= 1400

    def test_experienced_gets_near_level(self):
        veteran = PuzzleRating(rating=1700, rd=60.0, games=50)
        target = select_puzzle_rating(veteran, is_beginner=False)
        assert 1500 < target < 1800

    def test_deviation_floor_enforced(self):
        user = PuzzleRating(rating=1200, rd=350.0, games=5)
        for _ in range(50):
            user = update_puzzle_rating(user, 1200, True)
        assert user.rd >= 30.0


# ─────────────────────────────────────────────────────────────
# Unit tests: models (no DB)
# ─────────────────────────────────────────────────────────────
class TestModels:
    def test_solve_rate_zero_when_unplayed(self):
        p = Puzzle(fen="8/8/8/8/8/8/8/8", solution=[], rating=1200, times_played=0, times_solved=0)
        assert p.solve_rate == 0.0

    def test_solve_rate_percentage(self):
        p = Puzzle(fen="8/8/8/8/8/8/8/8", solution=[], rating=1200, times_played=100, times_solved=30)
        assert p.solve_rate == 30.0

    def test_accuracy_zero_when_no_games(self):
        r = UserPuzzleRating(user_id="u1", puzzles_solved=0, puzzles_failed=0)
        assert r.accuracy == 0.0

    def test_accuracy_percentage(self):
        r = UserPuzzleRating(user_id="u1", puzzles_solved=7, puzzles_failed=3)
        assert r.accuracy == 70.0


# ─────────────────────────────────────────────────────────────
# Model behaviour with DB
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestStreaks:
    def test_first_puzzle_starts_streak_at_one(self):
        s = PuzzleStreak.objects.create(user_id="u1")
        s.update_streak(date(2026, 1, 1))
        assert s.current_streak == 1
        assert s.longest_streak == 1

    def test_consecutive_day_increments(self):
        s = PuzzleStreak.objects.create(user_id="u1")
        s.update_streak(date(2026, 1, 1))
        s.update_streak(date(2026, 1, 2))
        assert s.current_streak == 2

    def test_gap_resets_streak(self):
        s = PuzzleStreak.objects.create(user_id="u1")
        s.update_streak(date(2026, 1, 1))
        s.update_streak(date(2026, 1, 2))
        s.update_streak(date(2026, 1, 10))  # 8-day gap
        assert s.current_streak == 1

    def test_same_day_does_not_double_count(self):
        s = PuzzleStreak.objects.create(user_id="u1")
        s.update_streak(date(2026, 1, 1))
        s.update_streak(date(2026, 1, 1))
        assert s.current_streak == 1
        assert s.total_solved == 1

    def test_longest_streak_is_tracked(self):
        s = PuzzleStreak.objects.create(user_id="u1")
        for d in range(5):
            s.update_streak(date(2026, 1, 1) + timedelta(days=d))
        assert s.current_streak == 5
        assert s.longest_streak == 5

    def test_longest_streak_survives_reset(self):
        s = PuzzleStreak.objects.create(user_id="u1")
        for d in range(5):
            s.update_streak(date(2026, 1, 1) + timedelta(days=d))
        s.update_streak(date(2026, 2, 1))  # long gap resets current
        assert s.current_streak == 1
        assert s.longest_streak == 5
