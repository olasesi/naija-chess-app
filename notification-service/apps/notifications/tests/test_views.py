import pytest
from django.urls import reverse
from rest_framework import status
from apps.notifications.models import Notification
from .factories import NotificationFactory


@pytest.mark.django_db
class TestNotificationAPI:
    def _auth_header(self):
        """Build an auth header with a mock JWT matching what GatewayJWTAuthentication expects."""
        return {
            "HTTP_X_USER_ID": "user-123",
            "HTTP_X_USER_EMAIL": "test@example.com",
            "HTTP_X_USER_ROLE": "user",
        }

    def test_list_notifications(self, api_client):
        NotificationFactory.create_batch(5, recipient_id="user-123")
        NotificationFactory.create_batch(3, recipient_id="other-user")

        url = reverse("notification-list")
        response = api_client.get(url, **self._auth_header())

        assert response.status_code == status.HTTP_200_OK
        # APIJSONRenderer wraps in {success, message, data}
        body = response.json()
        assert body.get("success", True) is True
        results = body.get("data", body).get("results") or body.get("results") or body
        assert len(results) == 5

    def test_unread_count(self, api_client):
        NotificationFactory.create_batch(3, recipient_id="user-123")
        NotificationFactory.create(recipient_id="user-123", read_at="2024-01-01T00:00:00Z")

        url = reverse("notification-unread-count")
        response = api_client.get(url, **self._auth_header())

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_mark_as_read(self, api_client):
        notification = NotificationFactory(recipient_id="user-123")

        url = reverse("notification-read", kwargs={"pk": notification.id})
        response = api_client.post(url, **self._auth_header())

        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.read_at is not None

    def test_read_all(self, api_client):
        notifications = NotificationFactory.create_batch(5, recipient_id="user-123")

        url = reverse("notification-read-all")
        response = api_client.post(
            url,
            {"notification_ids": [n.id for n in notifications[:3]]},
            format="json",
            **self._auth_header(),
        )

        assert response.status_code == status.HTTP_200_OK
        for n in notifications[:3]:
            n.refresh_from_db()
            assert n.read_at is not None
        for n in notifications[3:]:
            n.refresh_from_db()
            assert n.read_at is None

    def test_filter_by_read_status(self, api_client):
        NotificationFactory.create_batch(3, recipient_id="user-123")
        read_notif = NotificationFactory(recipient_id="user-123", read_at="2024-01-01T00:00:00Z")

        url = reverse("notification-list") + "?read=true"
        response = api_client.get(url, **self._auth_header())
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        results = body.get("data", body).get("results") or body.get("results") or body
        assert len(results) == 1

        url = reverse("notification-list") + "?read=false"
        response = api_client.get(url, **self._auth_header())
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        results = body.get("data", body).get("results") or body.get("results") or body
        assert len(results) == 3

    def test_internal_send(self, api_client):
        url = reverse("internal-send")
        response = api_client.post(
            url,
            {
                "recipient_id": "user-456",
                "type": "game_invite",
                "title": "You're invited!",
                "body": "Play a game with me",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Notification.objects.count() == 1
        notification = Notification.objects.first()
        assert notification.recipient_id == "user-456"
        assert notification.type == "game_invite"
