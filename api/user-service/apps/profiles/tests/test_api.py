import pytest
from django.test import Client
from apps.profiles.models import UserProfile


@pytest.mark.django_db
class TestProfileAPI:
    def test_get_profile_creates_if_not_exists(self):
        client = Client()
        response = client.get(
            "/api/users/profiles/me",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "test@test.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        assert UserProfile.objects.filter(userId="test-user-1").exists()

    def test_update_profile(self):
        UserProfile.objects.create(userId="test-user-1")
        client = Client()
        response = client.patch(
            "/api/users/profiles/me",
            {"displayName": "TestPlayer", "country": "US"},
            content_type="application/json",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "test@test.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        profile = UserProfile.objects.get(userId="test-user-1")
        assert profile.displayName == "TestPlayer"
        assert profile.country == "US"

    def test_search_profiles(self):
        UserProfile.objects.create(userId="user-1", displayName="AliceWonder")
        UserProfile.objects.create(userId="user-2", displayName="BobBuilder")
        client = Client()
        response = client.get(
            "/api/users/profiles/search?q=Ali",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "test@test.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1
