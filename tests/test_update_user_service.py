import pytest
from auth.models import User
from auth.repository import UserRepository
from auth.password_hasher import PasswordHasher
from auth.schemas import UpdateUserSchema
from auth.update_user_service import UpdateUserService


@pytest.fixture
def repo(app):
    return UserRepository()


@pytest.fixture
def hasher(app):
    return PasswordHasher()


@pytest.fixture
def service(repo, hasher):
    return UpdateUserService(repo, hasher)


@pytest.fixture
def existing_user(repo, hasher):
    user = User(
        username="alice",
        email="alice@example.com",
        password_hash=hasher.hash("secret123"),
    )
    return repo.save(user)


def _schema(**kwargs):
    defaults = {"current_password": "secret123"}
    return UpdateUserSchema.from_dict({**defaults, **kwargs})


# ---------------------------------------------------------------------------
# UpdateUserSchema
# ---------------------------------------------------------------------------

class TestUpdateUserSchema:
    def test_valid_only_current_password(self):
        s = _schema() #arrage
        assert s.current_password == "secret123"

    def test_valid_all_fields(self):
        s = _schema(username="bob", email="bob@example.com", new_password="newpass1") #arrange
        assert s.username == "bob"
        assert s.email == "bob@example.com"
        assert s.new_password == "newpass1"

    def test_missing_current_password_raises(self):
        with pytest.raises(ValueError) as exc:
            UpdateUserSchema.from_dict({"username": "bob"})
        assert "current_password" in exc.value.args[0]

    def test_empty_current_password_raises(self):
        with pytest.raises(ValueError) as exc:
            UpdateUserSchema.from_dict({"current_password": ""})
        assert "current_password" in exc.value.args[0]

    def test_username_too_long_raises(self):
        with pytest.raises(ValueError) as exc:
            _schema(username="x" * 81)
        assert "username" in exc.value.args[0]

    def test_email_without_at_raises(self):
        with pytest.raises(ValueError) as exc:
            _schema(email="notanemail")
        assert "email" in exc.value.args[0]

    def test_email_too_long_raises(self):
        with pytest.raises(ValueError) as exc:
            _schema(email="a@" + "b" * 120)
        assert "email" in exc.value.args[0]

    def test_new_password_too_short_raises(self):
        with pytest.raises(ValueError) as exc:
            _schema(new_password="abc")
        assert "new_password" in exc.value.args[0]

    def test_new_password_too_long_raises(self):
        with pytest.raises(ValueError) as exc:
            _schema(new_password="x" * 73)
        assert "new_password" in exc.value.args[0]

    def test_multiple_invalid_fields_collects_all_errors(self):
        with pytest.raises(ValueError) as exc:
            UpdateUserSchema.from_dict({"email": "bad", "new_password": "ab"})
        errors = exc.value.args[0]
        assert "current_password" in errors
        assert "email" in errors
        assert "new_password" in errors

    def test_strips_whitespace_from_username(self):
        s = _schema(username="  bob  ")
        assert s.username == "bob"

    def test_strips_whitespace_from_email(self):
        s = _schema(email="  bob@example.com  ")
        assert s.email == "bob@example.com"

    def test_whitespace_only_username_treated_as_none(self):
        s = _schema(username="   ")
        assert s.username is None

    def test_none_body_raises(self):
        with pytest.raises(ValueError) as exc:
            UpdateUserSchema.from_dict(None)
        assert "current_password" in exc.value.args[0]


# ---------------------------------------------------------------------------
# UpdateUserService
# ---------------------------------------------------------------------------

class TestUpdateUserService:
    def test_update_username(self, service, existing_user):
        schema = _schema(username="alice2") #arrange
        user = service.execute(existing_user.id, schema) ## act
        assert user.username == "alice2" ##assert

    def test_update_email(self, service, existing_user):
        schema = _schema(email="new@example.com")
        user = service.execute(existing_user.id, schema)
        assert user.email == "new@example.com"

    def test_update_password_new_hash_verifiable(self, service, existing_user, hasher):
        schema = _schema(new_password="newpass99")
        user = service.execute(existing_user.id, schema)
        assert hasher.verify("newpass99", user.password_hash)

    def test_update_password_old_password_no_longer_valid(self, service, existing_user, hasher):
        schema = _schema(new_password="newpass99")
        user = service.execute(existing_user.id, schema)
        assert not hasher.verify("secret123", user.password_hash)

    def test_update_all_fields(self, service, existing_user, hasher):
        schema = _schema(username="alice2", email="new@example.com", new_password="newpass99")
        user = service.execute(existing_user.id, schema)
        assert user.username == "alice2"
        assert user.email == "new@example.com"
        assert hasher.verify("newpass99", user.password_hash)

    def test_no_fields_changed_returns_same_user(self, service, existing_user):
        schema = _schema()
        user = service.execute(existing_user.id, schema)
        assert user.username == existing_user.username
        assert user.email == existing_user.email

    def test_same_username_does_not_raise(self, service, existing_user):
        schema = _schema(username="alice")
        user = service.execute(existing_user.id, schema)
        assert user.username == "alice"

    def test_same_email_does_not_raise(self, service, existing_user):
        schema = _schema(email="alice@example.com")
        user = service.execute(existing_user.id, schema)
        assert user.email == "alice@example.com"

    def test_wrong_current_password_raises_value_error(self, service, existing_user):
        schema = _schema(username="hacker", current_password="wrongpass")
        with pytest.raises(ValueError) as exc:
            service.execute(existing_user.id, schema)
        assert "current_password" in exc.value.args[0]

    def test_nonexistent_user_raises_lookup_error(self, service):
        schema = _schema()
        with pytest.raises(LookupError) as exc:
            service.execute(9999, schema)
        assert "user" in exc.value.args[0]

    def test_duplicate_username_raises_value_error(self, service, existing_user, repo, hasher):
        other = User(username="bob", email="bob@example.com", password_hash=hasher.hash("bobpass1"))
        repo.save(other)
        schema = _schema(username="bob")
        with pytest.raises(ValueError) as exc:
            service.execute(existing_user.id, schema)
        assert "username" in exc.value.args[0]

    def test_duplicate_email_raises_value_error(self, service, existing_user, repo, hasher):
        other = User(username="bob", email="bob@example.com", password_hash=hasher.hash("bobpass1"))
        repo.save(other)
        schema = _schema(email="bob@example.com")
        with pytest.raises(ValueError) as exc:
            service.execute(existing_user.id, schema)
        assert "email" in exc.value.args[0]
