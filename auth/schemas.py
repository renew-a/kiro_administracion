def _str_field(data: dict, key: str) -> str:
    value = data.get(key) or ""
    return value.strip() if isinstance(value, str) else ""


class RegisterSchema:
    def __init__(self, username: str, email: str, password: str) -> None:
        self.username = username
        self.email = email
        self.password = password

    @classmethod
    def from_dict(cls, data: dict | None) -> "RegisterSchema":
        data = data or {}
        errors: dict[str, str] = {}

        username = _str_field(data, "username")
        if not username or len(username) > 80:
            errors["username"] = "El nombre de usuario es obligatorio."

        email = _str_field(data, "email")
        if not email or "@" not in email or len(email) > 120:
            errors["email"] = "Correo electrónico inválido."

        password = _str_field(data, "password")
        if not (6 <= len(password) <= 72):
            errors["password"] = "La contraseña debe tener al menos 6 caracteres."

        if errors:
            raise ValueError(errors)

        return cls(username=username, email=email, password=password)


class UpdateUserSchema:
    def __init__(self, username: str | None, email: str | None, new_password: str | None, current_password: str) -> None:
        self.username = username
        self.email = email
        self.new_password = new_password
        self.current_password = current_password

    @classmethod
    def from_dict(cls, data: dict | None) -> "UpdateUserSchema":
        data = data or {}
        errors: dict[str, str] = {}

        current_password = _str_field(data, "current_password")
        if not current_password:
            errors["current_password"] = "La contraseña actual es obligatoria."

        username = _str_field(data, "username") or None
        if username is not None and len(username) > 80:
            errors["username"] = "El nombre de usuario es obligatorio."

        email = _str_field(data, "email") or None
        if email is not None and ("@" not in email or len(email) > 120):
            errors["email"] = "Correo electrónico inválido."

        new_password = _str_field(data, "new_password") or None
        if new_password is not None and not (6 <= len(new_password) <= 72):
            errors["new_password"] = "La contraseña debe tener al menos 6 caracteres."

        if errors:
            raise ValueError(errors)

        return cls(username=username, email=email, new_password=new_password, current_password=current_password)


class LoginSchema:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

    @classmethod
    def from_dict(cls, data: dict | None) -> "LoginSchema":
        data = data or {}
        errors: dict[str, str] = {}

        email = _str_field(data, "email")
        if not email or "@" not in email:
            errors["email"] = "Correo electrónico inválido."

        password = _str_field(data, "password")
        if not password:
            errors["password"] = "La contraseña es obligatoria."

        if errors:
            raise ValueError(errors)

        return cls(email=email, password=password)
