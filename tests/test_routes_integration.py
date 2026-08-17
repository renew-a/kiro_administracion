"""Integration tests for POST /auth/register and POST /auth/login routes."""
import json
import pytest


VALID_REGISTER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepass",
}

VALID_LOGIN = {
    "email": "test@example.com",
    "password": "securepass",
}


def post_json(client, url, data):
    return client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Register — happy path
# ---------------------------------------------------------------------------

def test_register_valid_returns_201(client):
    resp = post_json(client, "/auth/register", VALID_REGISTER)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["message"] == "Usuario registrado."
    assert "id" in body


# ---------------------------------------------------------------------------
# Register — duplicate email / username
# ---------------------------------------------------------------------------

def test_register_duplicate_email_returns_409(client):
    post_json(client, "/auth/register", VALID_REGISTER)
    resp = post_json(
        client,
        "/auth/register",
        {**VALID_REGISTER, "username": "otheruser"},
    )
    assert resp.status_code == 409
    body = resp.get_json()
    assert "email" in body["errors"]


def test_register_duplicate_username_returns_409(client):
    post_json(client, "/auth/register", VALID_REGISTER)
    resp = post_json(
        client,
        "/auth/register",
        {**VALID_REGISTER, "email": "other@example.com"},
    )
    assert resp.status_code == 409
    body = resp.get_json()
    assert "username" in body["errors"]


# ---------------------------------------------------------------------------
# Register — invalid field validation (422)
# ---------------------------------------------------------------------------

def test_register_missing_username_returns_422(client):
    resp = post_json(client, "/auth/register", {"email": "a@b.com", "password": "abc123"})
    assert resp.status_code == 422
    assert "username" in resp.get_json()["errors"]


def test_register_whitespace_username_returns_422(client):
    resp = post_json(client, "/auth/register", {"username": "   ", "email": "a@b.com", "password": "abc123"})
    assert resp.status_code == 422
    assert "username" in resp.get_json()["errors"]


def test_register_invalid_email_returns_422(client):
    resp = post_json(client, "/auth/register", {"username": "user1", "email": "notanemail", "password": "abc123"})
    assert resp.status_code == 422
    assert "email" in resp.get_json()["errors"]


def test_register_short_password_returns_422(client):
    resp = post_json(client, "/auth/register", {"username": "user1", "email": "a@b.com", "password": "abc"})
    assert resp.status_code == 422
    assert "password" in resp.get_json()["errors"]


def test_register_all_invalid_fields_returns_422_with_all_errors(client):
    resp = post_json(client, "/auth/register", {"username": "", "email": "bad", "password": "ab"})
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]
    assert "username" in errors
    assert "email" in errors
    assert "password" in errors


def test_register_empty_body_returns_422(client):
    resp = post_json(client, "/auth/register", {})
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]
    # All required fields must be listed
    assert len(errors) >= 1


def test_register_non_json_body_returns_422(client):
    resp = client.post("/auth/register", data="not json", content_type="text/plain")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login — happy path
# ---------------------------------------------------------------------------

def test_login_valid_returns_200(client):
    post_json(client, "/auth/register", VALID_REGISTER)
    resp = post_json(client, "/auth/login", VALID_LOGIN)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["message"] == "Login exitoso."
    assert "id" in body
    assert body["username"] == VALID_REGISTER["username"]


# ---------------------------------------------------------------------------
# Login — wrong credentials (401)
# ---------------------------------------------------------------------------

def test_login_wrong_password_returns_401(client):
    post_json(client, "/auth/register", VALID_REGISTER)
    resp = post_json(client, "/auth/login", {"email": "test@example.com", "password": "wrongpass"})
    assert resp.status_code == 401
    assert "credentials" in resp.get_json()["errors"]


def test_login_unknown_email_returns_401(client):
    resp = post_json(client, "/auth/login", {"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401
    assert "credentials" in resp.get_json()["errors"]


# ---------------------------------------------------------------------------
# Login — invalid input (422)
# ---------------------------------------------------------------------------

def test_login_invalid_email_returns_422(client):
    resp = post_json(client, "/auth/login", {"email": "notanemail", "password": "abc123"})
    assert resp.status_code == 422
    assert "email" in resp.get_json()["errors"]


def test_login_missing_password_returns_422(client):
    resp = post_json(client, "/auth/login", {"email": "a@b.com"})
    assert resp.status_code == 422
    assert "password" in resp.get_json()["errors"]


def test_login_both_invalid_returns_422_with_both_errors(client):
    resp = post_json(client, "/auth/login", {"email": "bad", "password": ""})
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]
    assert "email" in errors
    assert "password" in errors


# ---------------------------------------------------------------------------
# Full register → login cycle
# ---------------------------------------------------------------------------

def test_register_then_login_cycle(client):
    reg = post_json(client, "/auth/register", VALID_REGISTER)
    assert reg.status_code == 201
    reg_id = reg.get_json()["id"]

    login = post_json(client, "/auth/login", VALID_LOGIN)
    assert login.status_code == 200
    body = login.get_json()
    assert body["id"] == reg_id
    assert body["username"] == VALID_REGISTER["username"]
