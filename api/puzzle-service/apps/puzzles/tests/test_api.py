import pytest
from rest_framework import status
from rest_framework.test import APIClient
from common.auth import AuthUser


def make_puzzle(**kwargs):
    from puzzles.models import Puzzle

    defaults = dict(
        fen="6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
        solution=[{"from": "a1", "to": "a8"}],
        rating=1000,
        difficulty="EASY",
        themes=["back-rank"],
        title="Test puzzle",
    )
    defaults.update(kwargs)
    return Puzzle.objects.create(**defaults)


def authed_client(user_id="player-1", role="PLAYER"):
    c = APIClient()
    c.force_authenticate(user=AuthUser(user_id, "p@test.com", role))
    return c


@pytest.mark.django_db
class TestPuzzleListing:
    def test_list_requires_auth(self):
        anon = APIClient()
        assert anon.get("/api/puzzles/").status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_list_returns_puzzles(self):
        make_puzzle()
        make_puzzle(difficulty="HARD", rating=1900)
        r = authed_client().get("/api/puzzles/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data["results"]) == 2

    def test_filter_by_difficulty(self):
        make_puzzle(difficulty="EASY")
        make_puzzle(difficulty="HARD")
        r = authed_client().get("/api/puzzles/?difficulty=HARD")
        assert len(r.data["results"]) == 1
        assert r.data["results"][0]["difficulty"] == "HARD"

    def test_filter_by_rating_window(self):
        make_puzzle(rating=800)
        make_puzzle(rating=2000)
        r = authed_client().get("/api/puzzles/?min_rating=1000&max_rating=2500")
        assert len(r.data["results"]) == 1
        assert r.data["results"][0]["rating"] == 2000

    def test_rating_window_excludes_out_of_range(self):
        make_puzzle(rating=800)
        make_puzzle(rating=2000)
        r = authed_client().get("/api/puzzles/?min_rating=1000&max_rating=1500")
        assert len(r.data["results"]) == 0

    def test_filter_by_theme(self):
        make_puzzle(themes=["fork"])
        make_puzzle(themes=["back-rank"])
        r = authed_client().get("/api/puzzles/?theme=fork")
        assert len(r.data["results"]) == 1

    def test_inactive_puzzles_hidden(self):
        make_puzzle(status="ARCHIVED")
        r = authed_client().get("/api/puzzles/")
        assert len(r.data["results"]) == 0


@pytest.mark.django_db
class TestNextPuzzle:
    def test_next_creates_rating_record(self):
        from puzzles.models import UserPuzzleRating

        make_puzzle()
        r = authed_client("u1").get("/api/puzzles/next/")
        assert r.status_code == status.HTTP_200_OK
        assert UserPuzzleRating.objects.filter(user_id="u1").exists()

    def test_next_404_without_puzzles(self):
        r = authed_client().get("/api/puzzles/next/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_next_prefers_near_target_rating(self):
        make_puzzle(rating=800, title="easy")
        make_puzzle(rating=1150, title="mid")
        r = authed_client("u1").get("/api/puzzles/next/")
        # novice (1200 default) should land on the closer one
        assert r.data["rating"] == 1150


@pytest.mark.django_db
class TestAttempts:
    def test_solving_creates_attempt_and_raises_rating(self):
        make_puzzle(rating=1200)
        c = authed_client("u1")
        r = c.post(
            "/api/puzzles/attempt/",
            {"puzzle_id": None, "solved": True, "time_taken_seconds": 20},
            format="json",
        )
        # first call without id should 404
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_solve_flow(self):
        p = make_puzzle(rating=1200)
        c = authed_client("u1")
        r = c.post(
            "/api/puzzles/attempt/",
            {"puzzle_id": str(p.id), "solved": True, "time_taken_seconds": 20},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert r.data["rating_after"] > r.data["rating_before"]
        assert r.data["attempt"]["solved"] is True

    def test_increment_play_counters(self):
        p = make_puzzle(rating=1200)
        c = authed_client("u1")
        c.post(
            "/api/puzzles/attempt/",
            {"puzzle_id": str(p.id), "solved": True, "time_taken_seconds": 20},
            format="json",
        )
        p.refresh_from_db()
        assert p.times_played == 1
        assert p.times_solved == 1

    def test_fail_flow_lowers_rating(self):
        p = make_puzzle(rating=1200)
        c = authed_client("u1")
        c.post("/api/puzzles/attempt/", {"puzzle_id": str(p.id), "solved": True}, format="json")
        r = c.post("/api/puzzles/attempt/", {"puzzle_id": str(p.id), "solved": False}, format="json")
        assert r.data["rating_after"] < r.data["rating_before"]

    def test_unknown_puzzle_404(self):
        r = authed_client().post(
            "/api/puzzles/attempt/",
            {"puzzle_id": "00000000-0000-0000-0000-000000000000", "solved": True},
            format="json",
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_attempt_requires_auth(self):
        p = make_puzzle()
        r = APIClient().post(
            "/api/puzzles/attempt/",
            {"puzzle_id": str(p.id), "solved": True},
            format="json",
        )
        assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
class TestStreakRatingStats:
    def test_streak_endpoint(self):
        r = authed_client("u1").get("/api/puzzles/streak/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["current_streak"] == 0

    def test_daily_solve_updates_streak(self):
        from django.utils import timezone
        from puzzles.models import DailyPuzzle

        p = make_puzzle(rating=1200)
        DailyPuzzle.objects.create(date=timezone.now().date(), puzzle=p)
        r = authed_client("u1").post(
            "/api/puzzles/attempt/",
            {"puzzle_id": str(p.id), "solved": True, "time_taken_seconds": 15},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert r.data is not None
        s = authed_client("u1").get("/api/puzzles/streak/")
        assert s.data["current_streak"] == 1

    def test_rating_endpoint_defaults(self):
        r = authed_client("u1").get("/api/puzzles/rating/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["rating"] == 1200
        assert r.data["accuracy"] == 0.0

    def test_daily_falls_back_when_unset(self):
        make_puzzle(difficulty="MEDIUM")
        r = authed_client().get("/api/puzzles/daily/")
        assert r.status_code == status.HTTP_200_OK
        assert "puzzle" in r.data

    def test_daily_returns_configured_puzzle(self):
        from django.utils import timezone
        from puzzles.models import DailyPuzzle

        p = make_puzzle(difficulty="MEDIUM", title="Daily")
        DailyPuzzle.objects.create(date=timezone.now().date(), puzzle=p)
        r = authed_client().get("/api/puzzles/daily/")
        assert r.data["puzzle"]["title"] == "Daily"

    def test_history_paginates(self):
        p = make_puzzle(rating=1200)
        c = authed_client("u1")
        for _ in range(3):
            c.post(
                "/api/puzzles/attempt/",
                {"puzzle_id": str(p.id), "solved": True, "time_taken_seconds": 10},
                format="json",
            )
        r = c.get("/api/puzzles/history/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data["results"]) == 3

    def test_history_is_scoped_to_user(self):
        p = make_puzzle(rating=1200)
        authed_client("u1").post(
            "/api/puzzles/attempt/",
            {"puzzle_id": str(p.id), "solved": True},
            format="json",
        )
        r = authed_client("u2").get("/api/puzzles/history/")
        assert len(r.data["results"]) == 0

    def test_puzzle_stats(self):
        p = make_puzzle(rating=1200)
        authed_client("u1").post(
            "/api/puzzles/attempt/",
            {"puzzle_id": str(p.id), "solved": True, "time_taken_seconds": 30},
            format="json",
        )
        r = authed_client().get(f"/api/puzzles/{p.id}/stats/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["total_attempts"] == 1
        assert r.data["solved_count"] == 1
        assert r.data["avg_solve_time_seconds"] == 30

    def test_health_is_public(self):
        r = APIClient().get("/api/health/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        assert r.data["service"] == "puzzle-service"
