import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock

from tournaments.models import Tournament, TournamentPlayer, TournamentRound, TournamentMatch
from common.auth import AuthUser


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    client = APIClient()
    user = AuthUser("user-1", "test@test.com", "PLAYER")
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client():
    from rest_framework.test import APIClient
    client = APIClient()
    user = AuthUser("admin-1", "admin@test.com", "ADMIN")
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def tournament_data():
    return {
        "name": "Test Swiss",
        "description": "A test tournament",
        "type": "SWISS",
        "time_control_initial": 600,
        "time_control_increment": 5,
        "max_players": 16,
        "min_players": 2,
        "total_rounds": 5,
    }


@pytest.mark.django_db
class TestTournamentCreate:
    def test_create_tournament(self, api_client, tournament_data):
        resp = api_client.post(reverse("tournament-list"), tournament_data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["name"] == "Test Swiss"
        assert resp.data["type"] == "SWISS"
        assert resp.data["status"] == "PENDING"
        assert resp.data["creator_id"] == "user-1"

    def test_create_tournament_unauthenticated(self, tournament_data):
        from rest_framework.test import APIClient
        client = APIClient()
        resp = client.post(reverse("tournament-list"), tournament_data, format="json")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
class TestTournamentJoinLeave:
    def test_join_tournament(self, api_client):
        t = Tournament.objects.create(name="Test", type="SWISS", creator_id="other-user")
        resp = api_client.post(reverse("tournament-join", args=[t.id]))
        assert resp.status_code == status.HTTP_201_CREATED
        assert TournamentPlayer.objects.filter(tournament=t, user_id="user-1").exists()

    def test_join_twice(self, api_client):
        t = Tournament.objects.create(name="Test", type="SWISS", creator_id="other-user")
        TournamentPlayer.objects.create(tournament=t, user_id="user-1")
        resp = api_client.post(reverse("tournament-join", args=[t.id]))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_leave_pending(self, api_client):
        t = Tournament.objects.create(name="Test", type="SWISS", creator_id="other-user")
        TournamentPlayer.objects.create(tournament=t, user_id="user-1")
        resp = api_client.post(reverse("tournament-leave", args=[t.id]))
        assert resp.status_code == status.HTTP_200_OK
        assert not TournamentPlayer.objects.filter(tournament=t, user_id="user-1").exists()

    def test_leave_active_tournament_fails(self, api_client):
        t = Tournament.objects.create(name="Test", type="SWISS", status="ACTIVE", creator_id="other-user")
        TournamentPlayer.objects.create(tournament=t, user_id="user-1")
        resp = api_client.post(reverse("tournament-leave", args=[t.id]))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTournamentStart:
    def test_start_by_creator(self, api_client):
        t = Tournament.objects.create(name="Test", type="SWISS", creator_id="user-1", min_players=2)
        TournamentPlayer.objects.create(tournament=t, user_id="p1", seed=1)
        TournamentPlayer.objects.create(tournament=t, user_id="p2", seed=2)

        resp = api_client.post(reverse("tournament-start", args=[t.id]))
        assert resp.status_code == status.HTTP_200_OK
        t.refresh_from_db()
        assert t.status == "ACTIVE"
        assert t.current_round == 1

    def test_start_by_non_creator_fails(self, api_client):
        t = Tournament.objects.create(name="Test", type="SWISS", creator_id="other-user")
        TournamentPlayer.objects.create(tournament=t, user_id="p1", seed=1)
        resp = api_client.post(reverse("tournament-start", args=[t.id]))
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTournamentMatches:
    def test_list_tournaments(self, api_client):
        Tournament.objects.create(name="T1", type="SWISS", creator_id="u1")
        Tournament.objects.create(name="T2", type="ROUND_ROBIN", creator_id="u2")
        resp = api_client.get(reverse("tournament-list"))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2
        assert len(resp.data["results"]) == 2

    def test_filter_by_status(self, api_client):
        Tournament.objects.create(name="T1", type="SWISS", status="PENDING", creator_id="u1")
        Tournament.objects.create(name="T2", type="SWISS", status="ACTIVE", creator_id="u2")
        resp = api_client.get(reverse("tournament-list"), {"status": "ACTIVE"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["status"] == "ACTIVE"

    def test_my_tournaments(self, api_client):
        t = Tournament.objects.create(name="T1", type="SWISS", creator_id="other")
        TournamentPlayer.objects.create(tournament=t, user_id="user-1")
        resp = api_client.get(reverse("tournament-my"))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
