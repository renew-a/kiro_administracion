"""Unit tests for PasswordHasher (task 2.4)."""
import pytest
from auth.password_hasher import PasswordHasher


@pytest.fixture
def hasher(app):
    # app fixture ensures Flask app context + bcrypt is initialised
    return PasswordHasher()


def test_hash_returns_nonempty_string(hasher):
    result = hasher.hash("mysecret")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_raises_for_empty_string(hasher):
    with pytest.raises(ValueError):
        hasher.hash("")


def test_hash_raises_for_none(hasher):
    with pytest.raises(ValueError):
        hasher.hash(None)


def test_verify_returns_true_for_matching_pair(hasher):
    plain = "correct_password"
    hashed = hasher.hash(plain)
    assert hasher.verify(plain, hashed) is True


def test_verify_returns_false_for_mismatched_pair(hasher):
    hashed = hasher.hash("correct")
    assert hasher.verify("wrong", hashed) is False


def test_verify_returns_false_for_non_bcrypt_string(hasher):
    # Should not raise, just return False
    result = hasher.verify("anypassword", "not_a_bcrypt_hash")
    assert result is False
