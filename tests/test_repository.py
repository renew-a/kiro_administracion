"""Unit tests for UserRepository (task 3.2)."""
import pytest
from extensions import db
from auth.models import User
from auth.repository import UserRepository


@pytest.fixture
def repo(app):
    return UserRepository()


def _make_user(username="alice", email="alice@example.com", password_hash="hash1"):
    return User(username=username, email=email, password_hash=password_hash)


def test_save_persists_user_and_assigns_id(repo):
    user = _make_user()
    saved = repo.save(user)
    assert saved.id is not None


def test_find_by_email_returns_user(repo):
    repo.save(_make_user())
    found = repo.find_by_email("alice@example.com")
    assert found is not None
    assert found.email == "alice@example.com"


def test_find_by_email_returns_none_for_missing(repo):
    result = repo.find_by_email("nobody@example.com")
    assert result is None


def test_find_by_username_returns_user(repo):
    repo.save(_make_user())
    found = repo.find_by_username("alice")
    assert found is not None
    assert found.username == "alice"


def test_find_by_username_returns_none_for_missing(repo):
    result = repo.find_by_username("ghost")
    assert result is None
