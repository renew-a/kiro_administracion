from auth.models import User
from auth.repository import UserRepository
from auth.password_hasher import PasswordHasher
from auth.schemas import LoginSchema

_INVALID_CREDENTIALS = {"credentials": "Correo o contraseña incorrectos."}


class LoginService:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher) -> None:
        self._repo = repo
        self._hasher = hasher

    def execute(self, schema: LoginSchema) -> User:
        user = self._repo.find_by_email(schema.email)

        if not user or not self._hasher.verify(schema.password, user.password_hash):
            raise ValueError(_INVALID_CREDENTIALS)

        return user
