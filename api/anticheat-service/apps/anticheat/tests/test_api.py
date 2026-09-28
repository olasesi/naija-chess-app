import pytest
from rest_framework import status
from rest_framework.test import APIClient
from common.auth import AuthUser

from anticheat.models import CheatSignal, GameFlag, UserSanction


def authed_client(user_id="u1", role="PLAYER"):
    c = APIClient()
    c.force_authenticate(user=AuthUser(user_id, "p@test.com", role))
    return c


@pytest.mark.django_db
class TestSignals:
    def test_signals_requires_auth(self):
        r = APIClient().post(
            "/api/anticheat/signals/",
            {"signal_type": "engine_accuracy", "game_id": "g1", "value": 95},
            format="json",
        )
        assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_record_signal(self):
        r = authed_client().post(
            "/api/anticheat/signals/",
            {"signal_type": "engine_accuracy", "game_id": "g1", "value": 95},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert r.data["user_id"] == "u1"
        assert CheatSignal.objects.count() == 1

    def test_invalid_signal_type_rejected(self):
        r = authed_client().post(
            "/api/anticheat/signals/",
            {"signal_type": "bogus", "game_id": "g1", "value": 1},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_signals_by_game(self):
        c = authed_client()
        for game in ("g1", "g2"):
            c.post(
                "/api/anticheat/signals/",
                {"signal_type": "move_time_ms", "game_id": game, "value": 900},
                format="json",
            )
        r = c.get("/api/anticheat/signals/?game_id=g1")
        assert len(r.data["results"]) == 1
        assert r.data["results"][0]["game_id"] == "g1"


@pytest.mark.django_db
class TestFlags:
    def test_evaluate_clean(self):
        authed_client("sus").post(
            "/api/anticheat/signals/",
            {"signal_type": "engine_accuracy", "game_id": "g1", "value": 60},
            format="json",
        )
        r = authed_client("sus").post("/api/anticheat/flags/evaluate/", {"game_id": "g1"}, format="json")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["flagged"] is False
        assert not GameFlag.objects.exists()

    def test_evaluate_flags_suspicious(self):
        c = authed_client("sus")
        for _ in range(20):
            c.post(
                "/api/anticheat/signals/",
                {"signal_type": "engine_accuracy", "game_id": "g1", "value": 98},
                format="json",
            )
        r = c.post("/api/anticheat/flags/evaluate/", {"game_id": "g1"}, format="json")
        assert r.data["flagged"] is True
        assert GameFlag.objects.filter(game_id="g1").exists()

    def test_manual_flag(self):
        r = authed_client().post(
            "/api/anticheat/flags/",
            {"game_id": "g9"},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_flag_listing(self):
        GameFlag.objects.create(
            game_id="xyz", user_id="u1", suspicion_score=90, reasons=["x"]
        )
        r = authed_client().get("/api/anticheat/flags/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data["results"]) == 1

    def test_resolve_flag(self):
        f = GameFlag.objects.create(game_id="flagme", user_id="u1", suspicion_score=80, reasons=["r"])
        r = authed_client().post(
            "/api/anticheat/flags/resolve/",
            {"game_id": "flagme", "status": "CLEARED"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        f.refresh_from_db()
        assert f.status == "CLEARED"
        assert f.resolved_at is not None
        assert f.resolved_by == "u1"


@pytest.mark.django_db
class TestSanctions:
    def test_create_sanction(self):
        r = authed_client("admin", "ADMIN").post(
            "/api/anticheat/sanctions/",
            {"user_id": "cheater", "action": "WARNING", "reason": "suspected engine use"},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert UserSanction.objects.get(user_id="cheater").applied_by == "admin"

    def test_list_sanctions_filters_active(self):
        UserSanction.objects.create(user_id="c1", action="BANNED", active=True)
        r = authed_client().get("/api/anticheat/sanctions/?active=true")
        assert len(r.data["results"]) == 1


@pytest.mark.django_db
class TestUserRadar:
    def test_radar_defaults(self):
        r = authed_client().get("/api/anticheat/users/u1/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["open_flags"] == 0
        assert r.data["needs_sanction"] is False

    def test_radar_needs_sanction_after_flags(self):
        from django.conf import settings as s
        for i in range(s.ANTICHEAT_SANCTION_AFTER_FLAGS):
            GameFlag.objects.create(
                game_id=f"g{i}", user_id="u7", status="OPEN", suspicion_score=90, reasons=["r"]
            )
        r = authed_client().get("/api/anticheat/users/u7/")
        assert r.data["open_flags"] == s.ANTICHEAT_SANCTION_AFTER_FLAGS
        assert r.data["needs_sanction"] is True

    def test_health_is_public(self):
        r = APIClient().get("/api/health/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        assert r.data["service"] == "anticheat-service"