"""Preference API tests."""

from uuid import uuid4


def test_preferences_default_and_set(client):
    user_id = uuid4()
    got = client.get(f"/api/v1/users/{user_id}/preferences")
    assert got.status_code == 200
    prefs = got.json()["preferences"]
    assert prefs["email"] is True

    created = client.post(
        f"/api/v1/users/{user_id}/preferences",
        json={"channel": "sms", "enabled": False},
    )
    assert created.status_code == 201
    assert created.json()["enabled"] is False

    got2 = client.get(f"/api/v1/users/{user_id}/preferences")
    assert got2.json()["preferences"]["sms"] is False

    deleted = client.delete(f"/api/v1/users/{user_id}/preferences/sms")
    assert deleted.status_code == 204


def test_opt_out_blocks_send(client):
    user_id = uuid4()
    client.post(
        f"/api/v1/users/{user_id}/preferences",
        json={"channel": "email", "enabled": False},
    )
    resp = client.post(
        "/api/v1/notifications",
        json={
            "user_id": str(user_id),
            "channel": "email",
            "recipient": "a@b.com",
            "body": "Nope",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "preference_not_met"
