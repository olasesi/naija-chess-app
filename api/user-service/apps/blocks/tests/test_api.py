import pytest
from django.test import Client

from apps.blocks.models import UserBlock

AUTH = {
    "HTTP_X_USER_ID": "user-1",
    "HTTP_X_USER_EMAIL": "a@a.com",
    "HTTP_X_USER_ROLE": "PLAYER",
}


def authed_client(user_id="user-1"):
    client = Client()
    return client, {**AUTH, "HTTP_X_USER_ID": user_id}


@pytest.mark.django_db
class TestBlocksAPI:
    def test_block_user(self):
        client, auth = authed_client()
        response = client.post(
            "/api/users/blocks",
            {"blockedId": "00000000-0000-0000-0000-000000000002", "type": "BLOCK"},
            content_type="application/json",
            **auth,
        )
        assert response.status_code == 201
        assert UserBlock.objects.filter(userId="user-1", blockedId="00000000-0000-0000-0000-000000000002", type="BLOCK").exists()

    def test_mute_user(self):
        client, auth = authed_client()
        response = client.post(
            "/api/users/blocks",
            {"blockedId": "00000000-0000-0000-0000-000000000002", "type": "MUTE", "reason": "spam"},
            content_type="application/json",
            **auth,
        )
        assert response.status_code == 201

    def test_cannot_block_self(self):
        client, auth = authed_client("00000000-0000-0000-0000-000000000001")
        response = client.post(
            "/api/users/blocks",
            {"blockedId": "00000000-0000-0000-0000-000000000001", "type": "BLOCK"},
            content_type="application/json",
            **auth,
        )
        assert response.status_code == 400

    def test_duplicate_block_conflict(self):
        UserBlock.objects.create(userId="user-1", blockedId="00000000-0000-0000-0000-000000000002", type="BLOCK")
        client, auth = authed_client()
        response = client.post(
            "/api/users/blocks",
            {"blockedId": "00000000-0000-0000-0000-000000000002", "type": "BLOCK"},
            content_type="application/json",
            **auth,
        )
        assert response.status_code == 409

    def test_same_user_can_be_blocked_and_muted(self):
        UserBlock.objects.create(userId="user-1", blockedId="user-2", type="BLOCK")
        client, auth = authed_client()
        response = client.post(
            "/api/users/blocks",
            {"blockedId": "00000000-0000-0000-0000-000000000002", "type": "MUTE"},
            content_type="application/json",
            **auth,
        )
        assert response.status_code == 201

    def test_list_blocks(self):
        UserBlock.objects.create(userId="user-1", blockedId="user-2", type="BLOCK")
        UserBlock.objects.create(userId="user-1", blockedId="user-3", type="MUTE")
        client, auth = authed_client()
        response = client.get("/api/users/blocks", **auth)
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

    def test_list_blocks_filtered_by_type(self):
        UserBlock.objects.create(userId="user-1", blockedId="user-2", type="BLOCK")
        UserBlock.objects.create(userId="user-1", blockedId="user-3", type="MUTE")
        client, auth = authed_client()
        response = client.get("/api/users/blocks?type=BLOCK", **auth)
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["type"] == "BLOCK"

    def test_status_endpoint(self):
        UserBlock.objects.create(userId="user-1", blockedId="user-2", type="BLOCK")
        client, auth = authed_client()
        response = client.get("/api/users/blocks/status/user-2", **auth)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["blocking"] is True
        assert data["blockedBy"] is False

    def test_blocked_by_other_user(self):
        UserBlock.objects.create(userId="user-2", blockedId="user-1", type="BLOCK")
        client, auth = authed_client()
        response = client.get("/api/users/blocks/status/user-2", **auth)
        data = response.json()["data"]
        assert data["blocking"] is False
        assert data["blockedBy"] is True
        assert data["isBlocked"] is True

    def test_remove_relationship(self):
        UserBlock.objects.create(userId="user-1", blockedId="user-2", type="BLOCK")
        UserBlock.objects.create(userId="user-1", blockedId="user-2", type="MUTE")
        client, auth = authed_client()
        response = client.delete("/api/users/blocks/user-2", **auth)
        assert response.status_code == 200
        assert not UserBlock.objects.filter(userId="user-1", blockedId="user-2").exists()

    def test_requires_auth(self):
        client = Client()
        response = client.get("/api/users/blocks")
        assert response.status_code in (401, 403)