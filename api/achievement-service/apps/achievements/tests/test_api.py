import pytest
from rest_framework import status
from rest_framework.test import APIClient
from common.auth import AuthUser

from achievements.models import Achievement, UserXP


def make_achievement(**kwargs):
    defaults = dict(
        code="test_ach",
        name="Test",
        description="",
        category="game",
        icon="🏆",
        xp_reward=50,
        criteria={"event": "game_won", "operator": "gte", "value": 5, "mode": "count"},
    )
    defaults.update(kwargs)
    return Achievement.objects.create(**defaults)


def authed_client(user_id="player-1", role="PLAYER"):
    c = APIClient()
    c.force_authenticate(user=AuthUser(user_id, "p@test.com", role))
    return c


@pytest.mark.django_db
class TestCatalog:
    def test_list_requires_auth(self):
        assert APIClient().get("/api/achievements/").status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_list_paginated(self):
        make_achievement(code="a1")
        make_achievement(code="a2", category="social")
        r = authed_client().get("/api/achievements/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data["results"]) == 2

    def test_list_includes_user_status(self):
        make_achievement(code="a1")
        r = authed_client().get("/api/achievements/")
        row = r.data["results"][0]
        assert row["unlocked"] is False
        assert row["progress"] == 0
        assert row["progress_target"] == 5

    def test_detail_by_code(self):
        make_achievement(code="unique_code")
        r = authed_client().get("/api/achievements/unique_code/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["code"] == "unique_code"

    def test_detail_404(self):
        assert authed_client().get("/api/achievements/nope/").status_code == status.HTTP_404_NOT_FOUND

    def test_filter_by_category(self):
        make_achievement(code="a1", category="game")
        make_achievement(code="a2", category="social")
        r = authed_client().get("/api/achievements/?category=social")
        assert len(r.data["results"]) == 1
        assert r.data["results"][0]["code"] == "a2"


@pytest.mark.django_db
class TestEvent:
    def test_event_gives_xp_and_can_unlock(self):
        make_achievement(code="first_win", criteria={"event": "game_won", "value": 1, "mode": "set"})
        r = authed_client("u1").post("/api/achievements/event/", {"type": "game_won"}, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert r.data["unlocked"] == ["first_win"]
        assert r.data["xp_gained"] > 0

    def test_event_requires_type(self):
        r = authed_client().post("/api/achievements/event/", {}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_event_accumulates_progress(self):
        make_achievement(code="wins_5", criteria={"event": "game_won", "value": 5, "mode": "count"})
        c = authed_client("u1")
        for _ in range(4):
            c.post("/api/achievements/event/", {"type": "game_won"}, format="json")
        r = c.post("/api/achievements/event/", {"type": "game_won"}, format="json")
        assert r.data["unlocked"] == ["wins_5"]

    def test_event_requires_auth(self):
        r = APIClient().post("/api/achievements/event/", {"type": "game_won"}, format="json")
        assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
class TestMineXPLeaderboard:
    def test_mine_empty(self):
        r = authed_client("u1").get("/api/achievements/mine/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["unlocked_count"] == 0

    def test_xp_defaults(self):
        UserXP.objects.create(user_id="u1")
        r = authed_client("u1").get("/api/achievements/xp/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["level"] == 1
        assert r.data["total_xp"] == 0

    def test_leaderboard_orders_by_xp(self):
        UserXP.objects.create(user_id="u2", total_xp=500, level=6)
        UserXP.objects.create(user_id="u1", total_xp=9000, level=90)
        r = authed_client().get("/api/achievements/leaderboard/")
        assert r.data["results"][0]["user_id"] == "u1"
        assert r.data["results"][1]["user_id"] == "u2"

    def test_health_is_public(self):
        r = APIClient().get("/api/health/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        assert r.data["service"] == "achievement-service"