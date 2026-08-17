"""Unit tests for the User model constraints (task 1.2)."""
import pytest
import sqlalchemy.exc
from extensions import db
from auth.models import User


def test_save_user_assigns_id(app):
    user = User(username="alice", email="alice@example.com", password_hash="hash1")
    db.session.add(user)
    db.session.commit()
    assert user.id is not None


def test_duplicate_email_raises_integrity_error(app):
    u1 = User(username="alice", email="alice@example.com", password_hash="hash1")
    u2 = User(username="bob", email="alice@example.com", password_hash="hash2")
    db.session.add(u1)
    db.session.commit()
    db.session.add(u2)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.commit()


def test_duplicate_username_raises_integrity_error(app):
    u1 = User(username="alice", email="alice@example.com", password_hash="hash1")
    u2 = User(username="alice", email="other@example.com", password_hash="hash2")
    db.session.add(u1)
    db.session.commit()
    db.session.add(u2)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.commit()


def test_missing_username_raises_integrity_error(app):
    user = User(email="a@b.com", password_hash="hash1")
    db.session.add(user)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.commit()


def test_missing_email_raises_integrity_error(app):
    user = User(username="alice", password_hash="hash1")
    db.session.add(user)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.commit()


def test_missing_password_hash_raises_integrity_error(app):
    user = User(username="alice", email="alice@example.com")
    db.session.add(user)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.commit()
