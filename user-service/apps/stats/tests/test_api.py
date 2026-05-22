import pytest
from django.test import Client
from apps.stats.models import UserStats


@pytest.mark.django_db
class TestStatsAPI:
    def test_get_stats_creates_if_not_exists(self):
        client = Client()
        response = client.get(
            "/api/users/stats/me",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "test@test.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        assert UserStats.objects.filter(userId="test-user-1").exists()
        assert response.json()["data"]["bulletRating"] == 1200

    def test_record_game_result(self):
        UserStats.objects.create(userId="test-user-1")
        client = Client()
        response = client.post(
            "/api/users/stats/record",
            {"result": "win", "timeControl": "blitz", "opponentRating": 1300},
            content_type="application/json",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "test@test.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        stats = UserStats.objects.get(userId="test-user-1")
        assert stats.gamesPlayed == 1
        assert stats.wins == 1
        assert stats.blitzRating > 1200
