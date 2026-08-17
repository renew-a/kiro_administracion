import json
import pytest


VALID_USER = {"username": "alice", "email": "alice@example.com", "password": "secret123"}


def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")


def patch_json(client, url, data):
    return client.patch(url, data=json.dumps(data), content_type="application/json")


@pytest.fixture
def registered(client):
    resp = post_json(client, "/auth/register", VALID_USER)
    return resp.get_json()["id"]


def test_update_username(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {
        "username": "alice2",
        "current_password": "secret123",
    })
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "alice2"


def test_update_email(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {
        "email": "new@example.com",
        "current_password": "secret123",
    })
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "new@example.com"

def test_update_password(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {
        "new_password": "newpass99",
        "current_password": "secret123",
    })
    assert resp.status_code == 200

    login = post_json(client, "/auth/login", {"email": "alice@example.com", "password": "newpass99"})
    assert login.status_code == 200


def test_update_wrong_current_password_returns_409(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {
        "username": "hacker",
        "current_password": "wrongpass",
    })
    assert resp.status_code == 409
    assert "current_password" in resp.get_json()["errors"]


def test_update_nonexistent_user_returns_404(client):
    resp = patch_json(client, "/auth/users/9999", {
        "username": "ghost",
        "current_password": "whatever",
    })
    assert resp.status_code == 404


def test_update_duplicate_username_returns_409(client, registered):
    post_json(client, "/auth/register", {"username": "bob", "email": "bob@example.com", "password": "bobpass1"})
    resp = patch_json(client, f"/auth/users/{registered}", {
        "username": "bob",
        "current_password": "secret123",
    })
    assert resp.status_code == 409
    assert "username" in resp.get_json()["errors"]


def test_update_duplicate_email_returns_409(client, registered):
    post_json(client, "/auth/register", {"username": "bob", "email": "bob@example.com", "password": "bobpass1"})
    resp = patch_json(client, f"/auth/users/{registered}", {
        "email": "bob@example.com",
        "current_password": "secret123",
    })
    assert resp.status_code == 409
    assert "email" in resp.get_json()["errors"]


def test_update_missing_current_password_returns_422(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {"username": "alice2"})
    assert resp.status_code == 422
    assert "current_password" in resp.get_json()["errors"]


def test_update_invalid_email_returns_422(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {
        "email": "notanemail",
        "current_password": "secret123",
    })
    assert resp.status_code == 422
    assert "email" in resp.get_json()["errors"]


def test_update_short_new_password_returns_422(client, registered):
    resp = patch_json(client, f"/auth/users/{registered}", {
        "new_password": "abc",
        "current_password": "secret123",
    })
    assert resp.status_code == 422
    assert "new_password" in resp.get_json()["errors"]
