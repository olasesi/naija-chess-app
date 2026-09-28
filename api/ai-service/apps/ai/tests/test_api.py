import pytest
from rest_framework import status
from rest_framework.test import APIClient
from common.auth import AuthUser

from ai.models import AIGame


def authed_client(user_id="player-1", role="PLAYER"):
    c = APIClient()
    c.force_authenticate(user=AuthUser(user_id, "p@test.com", role))
    return c


@pytest.mark.django_db
class TestAnswerEndpoint:
    def test_requires_auth(self):
        r = APIClient().post("/api/ai/move/", {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}, format="json")
        assert r.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_returns_move(self):
        r = authed_client().post(
            "/api/ai/move/",
            {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "level": "easy"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert r.data["move"]["from"] in ("a1","b1","c1","d1","e1","f1","g1","h1","a2","b2","c2","d2","e2","f2","g2","h2")

    def test_invalid_fen_rejected(self):
        r = authed_client().post("/api/ai/move/", {"fen": "garbage"}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_game_over_position(self):
        r = authed_client().post(
            "/api/ai/move/",
            {"fen": "7k/5Q1K/8/8/8/8/8/8 b - - 0 1"},
            format="json",
        )
        assert r.data["game_over"] is True


@pytest.mark.django_db
class TestGameSession:
    def test_create_game(self):
        r = authed_client("p1").post(
            "/api/ai/games/", {"side": "w", "level": "medium"}, format="json"
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert r.data["result"] == "PENDING"
        assert AIGame.objects.filter(user_id="p1").count() == 1

    def test_create_as_black_ai_moves_first(self):
        r = authed_client("p1").post(
            "/api/ai/games/", {"side": "b", "level": "easy"}, format="json"
        )
        assert r.data["ai_move"] is not None
        assert len(r.data["moves"]) == 1

    def test_user_move_then_ai_reply(self):
        r = authed_client("p1").post(
            "/api/ai/games/", {"side": "w", "level": "easy"}, format="json"
        )
        game_id = r.data["id"]
        m = authed_client("p1").post(
            f"/api/ai/games/{game_id}/move/",
            {"from_square": "e2", "to_square": "e4"},
            format="json",
        )
        assert m.status_code == status.HTTP_200_OK
        assert m.data["ai_move"] is not None
        assert len(m.data["moves"]) == 2
        assert m.data["moves"][0] == "e4"

    def test_illegal_move_rejected(self):
        r = authed_client("p1").post(
            "/api/ai/games/", {"side": "w", "level": "easy"}, format="json"
        )
        game_id = r.data["id"]
        m = authed_client("p1").post(
            f"/api/ai/games/{game_id}/move/",
            {"from_square": "e2", "to_square": "e5"},
            format="json",
        )
        assert m.status_code == status.HTTP_400_BAD_REQUEST

    def test_game_scoped_to_user(self):
        authed_client("p1").post("/api/ai/games/", {"side": "w", "level": "medium"}, format="json")
        r = authed_client("p2").get("/api/ai/games/")
        assert len(r.data["results"]) == 0

    def test_checkmate_sets_result(self):
        r = authed_client("p1").post(
            "/api/ai/games/", {"side": "w", "level": "easy"}, format="json"
        )
        game_id = r.data["id"]
        # Scholar's mate setup — white to move the queen to f7#
        g = AIGame.objects.get(id=game_id)
        g.fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
        g.save()
        m = authed_client("p1").post(
            f"/api/ai/games/{game_id}/move/",
            {"from_square": "h5", "to_square": "f7"},
            format="json",
        )
        assert m.status_code == status.HTTP_200_OK
        assert m.data["result"] == "PLAYER_WIN"
        assert m.data["ai_move"] is None

    def test_history(self):
        authed_client("p1").post("/api/ai/games/", {"side": "w", "level": "easy"}, format="json")
        r = authed_client("p1").get("/api/ai/games/history/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data) == 1

    def test_pgn_present_in_detail(self):
        r = authed_client("p1").post(
            "/api/ai/games/", {"side": "w", "level": "easy"}, format="json"
        )
        assert "[Event" in r.data["pgn"]

    def test_health_is_public(self):
        r = APIClient().get("/api/health/")
        assert r.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        assert r.data["service"] == "ai-service"