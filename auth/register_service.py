from auth.models import User
from auth.repository import UserRepository
from auth.password_hasher import PasswordHasher
from auth.schemas import RegisterSchema


class RegisterService:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher) -> None:
        self._repo = repo
        self._hasher = hasher

    def execute(self, schema: RegisterSchema) -> User:
        if self._repo.find_by_email(schema.email):
            raise ValueError({"email": "El correo ya está registrado."})

        if self._repo.find_by_username(schema.username):
            raise ValueError({"username": "El nombre de usuario ya existe."})

        user = User(
            username=schema.username,
            email=schema.email,
            password_hash=self._hasher.hash(schema.password),
        )
        return self._repo.save(user)
