import pytest
from django.test import Client
from apps.friends.models import Friend


@pytest.mark.django_db
class TestFriendsAPI:
    def test_send_friend_request(self):
        client = Client()
        response = client.post(
            "/api/users/friends/request",
            {"friendId": "00000000-0000-0000-0000-000000000002"},
            content_type="application/json",
            **{"HTTP_X_USER_ID": "user-1", "HTTP_X_USER_EMAIL": "a@a.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 201
        assert Friend.objects.filter(userId="user-1").exists()

    def test_accept_friend_request(self):
        Friend.objects.create(userId="user-2", friendId="user-1")
        client = Client()
        response = client.patch(
            "/api/users/friends/request/user-2",
            {"action": "accept"},
            content_type="application/json",
            **{"HTTP_X_USER_ID": "user-1", "HTTP_X_USER_EMAIL": "a@a.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 200
        friend = Friend.objects.get(userId="user-2", friendId="user-1")
        assert friend.status == "ACCEPTED"

    def test_cannot_friend_self(self):
        client = Client()
        response = client.post(
            "/api/users/friends/request",
            {"friendId": "00000000-0000-0000-0000-000000000001"},
            content_type="application/json",
            **{"HTTP_X_USER_ID": "00000000-0000-0000-0000-000000000001", "HTTP_X_USER_EMAIL": "a@a.com", "HTTP_X_USER_ROLE": "PLAYER"},
        )
        assert response.status_code == 400
