"""Unit tests for RegisterSchema and LoginSchema (task 4.6)."""
import pytest
from auth.schemas import RegisterSchema, LoginSchema


# ---------------------------------------------------------------------------
# RegisterSchema — valid input
# ---------------------------------------------------------------------------

def test_register_schema_valid():
    s = RegisterSchema.from_dict({"username": "alice", "email": "alice@example.com", "password": "secret1"})
    assert s.username == "alice"
    assert s.email == "alice@example.com"
    assert s.password == "secret1"


def test_register_schema_strips_whitespace_from_username():
    s = RegisterSchema.from_dict({"username": "  bob  ", "email": "b@b.com", "password": "abcdef"})
    assert s.username == "bob"


def test_register_schema_strips_whitespace_from_email():
    s = RegisterSchema.from_dict({"username": "bob", "email": "  b@b.com  ", "password": "abcdef"})
    assert s.email == "b@b.com"


# ---------------------------------------------------------------------------
# RegisterSchema — invalid fields
# ---------------------------------------------------------------------------

def test_register_schema_missing_username_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"email": "a@b.com", "password": "abc123"})
    assert "username" in exc.value.args[0]


def test_register_schema_empty_username_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "", "email": "a@b.com", "password": "abc123"})
    assert "username" in exc.value.args[0]


def test_register_schema_whitespace_only_username_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "   ", "email": "a@b.com", "password": "abc123"})
    assert "username" in exc.value.args[0]


def test_register_schema_too_long_username_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "x" * 81, "email": "a@b.com", "password": "abc123"})
    assert "username" in exc.value.args[0]


def test_register_schema_missing_email_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "alice", "password": "abc123"})
    assert "email" in exc.value.args[0]


def test_register_schema_no_at_sign_email_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "alice", "email": "notanemail", "password": "abc123"})
    assert "email" in exc.value.args[0]


def test_register_schema_too_long_email_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "alice", "email": "a@" + "b" * 120, "password": "abc123"})
    assert "email" in exc.value.args[0]


def test_register_schema_password_too_short_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "alice", "email": "a@b.com", "password": "abc"})
    assert "password" in exc.value.args[0]


def test_register_schema_password_too_long_raises():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "alice", "email": "a@b.com", "password": "x" * 73})
    assert "password" in exc.value.args[0]


def test_register_schema_empty_body_raises_all_errors():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({})
    errors = exc.value.args[0]
    assert "username" in errors
    assert "email" in errors
    assert "password" in errors


def test_register_schema_none_body_raises_all_errors():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict(None)
    errors = exc.value.args[0]
    assert len(errors) >= 1


def test_register_schema_multi_field_collects_all_errors():
    with pytest.raises(ValueError) as exc:
        RegisterSchema.from_dict({"username": "", "email": "bad", "password": "ab"})
    errors = exc.value.args[0]
    assert "username" in errors
    assert "email" in errors
    assert "password" in errors


# ---------------------------------------------------------------------------
# LoginSchema — valid input
# ---------------------------------------------------------------------------

def test_login_schema_valid():
    s = LoginSchema.from_dict({"email": "alice@example.com", "password": "secret1"})
    assert s.email == "alice@example.com"
    assert s.password == "secret1"


# ---------------------------------------------------------------------------
# LoginSchema — invalid fields
# ---------------------------------------------------------------------------

def test_login_schema_missing_email_raises():
    with pytest.raises(ValueError) as exc:
        LoginSchema.from_dict({"password": "abc123"})
    assert "email" in exc.value.args[0]


def test_login_schema_no_at_sign_email_raises():
    with pytest.raises(ValueError) as exc:
        LoginSchema.from_dict({"email": "notanemail", "password": "abc123"})
    assert "email" in exc.value.args[0]


def test_login_schema_missing_password_raises():
    with pytest.raises(ValueError) as exc:
        LoginSchema.from_dict({"email": "a@b.com"})
    assert "password" in exc.value.args[0]


def test_login_schema_empty_password_raises():
    with pytest.raises(ValueError) as exc:
        LoginSchema.from_dict({"email": "a@b.com", "password": ""})
    assert "password" in exc.value.args[0]


def test_login_schema_both_invalid_collects_all_errors():
    with pytest.raises(ValueError) as exc:
        LoginSchema.from_dict({"email": "bad", "password": ""})
    errors = exc.value.args[0]
    assert "email" in errors
    assert "password" in errors
