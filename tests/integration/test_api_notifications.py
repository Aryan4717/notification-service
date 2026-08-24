"""API integration tests for notifications."""

from uuid import uuid4


def test_create_and_get_notification(client, user_id):
    payload = {
        "user_id": str(user_id),
        "channel": "email",
        "recipient": "user@example.com",
        "priority": "high",
        "subject": "Hello",
        "body": "World",
        "idempotency_key": "key-1",
    }
    resp = client.post("/api/v1/notifications", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] in {"pending", "sent", "delivered"}
    nid = data["id"]

    got = client.get(f"/api/v1/notifications/{nid}")
    assert got.status_code == 200
    assert got.json()["id"] == nid


def test_idempotent_create(client, user_id):
    payload = {
        "user_id": str(user_id),
        "channel": "email",
        "recipient": "user@example.com",
        "body": "Hello",
        "idempotency_key": "same-key",
    }
    r1 = client.post("/api/v1/notifications", json=payload)
    r2 = client.post("/api/v1/notifications", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


def test_list_user_notifications(client, user_id):
    client.post(
        "/api/v1/notifications",
        json={
            "user_id": str(user_id),
            "channel": "sms",
            "recipient": "+14155552671",
            "body": "Hi",
        },
    )
    resp = client.get(f"/api/v1/users/{user_id}/notifications")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_invalid_recipient(client, user_id):
    resp = client.post(
        "/api/v1/notifications",
        json={
            "user_id": str(user_id),
            "channel": "email",
            "recipient": "not-email",
            "body": "x",
        },
    )
    assert resp.status_code == 400


def test_assignment_alias_path(client, user_id):
    resp = client.post(
        "/notifications",
        json={
            "user_id": str(user_id),
            "channel": "push",
            "recipient": "token-abcdefg",
            "subject": "Ping",
            "body": "Pong",
        },
    )
    assert resp.status_code == 201
