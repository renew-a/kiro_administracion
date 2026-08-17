from auth.models import User
from auth.repository import UserRepository
from auth.password_hasher import PasswordHasher
from auth.schemas import UpdateUserSchema

_INVALID_CREDENTIALS = {"current_password": "Contraseña actual incorrecta."}


class UpdateUserService:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher) -> None:
        self._repo = repo
        self._hasher = hasher

    def execute(self, user_id: int, schema: UpdateUserSchema) -> User:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise LookupError({"user": "Usuario no encontrado."})

        if not self._hasher.verify(schema.current_password, user.password_hash):
            raise ValueError(_INVALID_CREDENTIALS)

        if schema.username and schema.username != user.username:
            if self._repo.find_by_username(schema.username):
                raise ValueError({"username": "El nombre de usuario ya existe."})
            user.username = schema.username

        if schema.email and schema.email != user.email:
            if self._repo.find_by_email(schema.email):
                raise ValueError({"email": "El correo ya está registrado."})
            user.email = schema.email

        if schema.new_password:
            user.password_hash = self._hasher.hash(schema.new_password)

        return self._repo.save(user)
