import pytest
from django.test import Client
from apps.preferences.models import UserPreference


@pytest.mark.django_db
class TestPreferencesAPI:
    def test_get_preferences_creates_if_not_exists(self):
        client = Client()
        response = client.get(
            "/api/users/preferences",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "a@a.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        assert UserPreference.objects.filter(userId="test-user-1").exists()

    def test_update_preferences(self):
        UserPreference.objects.create(userId="test-user-1")
        client = Client()
        response = client.patch(
            "/api/users/preferences",
            {"theme": "light", "boardStyle": "wood"},
            content_type="application/json",
            **{"HTTP_X_USER_ID": "test-user-1", "HTTP_X_USER_EMAIL": "a@a.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        pref = UserPreference.objects.get(userId="test-user-1")
        assert pref.theme == "light"
        assert pref.boardStyle == "wood"
