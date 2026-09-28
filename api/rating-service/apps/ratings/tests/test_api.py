import pytest
from django.test import Client
from apps.ratings.models import PlayerRating, RatingHistory


@pytest.mark.django_db
class TestRatingAPI:
    def test_get_rating_me(self):
        PlayerRating.objects.create(userId="user-1", timeControl="rapid", rating=1600)
        client = Client()
        response = client.get(
            "/api/ratings/me",
            **{"HTTP_X_USER_ID": "user-1", "HTTP_X_USER_EMAIL": "a@a.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
        assert response.json()["data"][0]["rating"] == 1600

    def test_leaderboard_public(self):
        PlayerRating.objects.create(userId="user-1", timeControl="rapid", rating=1800, gamesPlayed=50)
        PlayerRating.objects.create(userId="user-2", timeControl="rapid", rating=1600, gamesPlayed=30)
        client = Client()

        # Should work without auth (public endpoint)
        response = client.get("/api/ratings/leaderboard/rapid")
        assert response.status_code == 200
