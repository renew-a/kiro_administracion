from extensions import bcrypt


class PasswordHasher:
    def hash(self, plain: str) -> str:
        if not plain:
            raise ValueError("Password must not be empty or None.")
        return bcrypt.generate_password_hash(plain).decode("utf-8")

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.check_password_hash(hashed, plain)
        except Exception:
            return False
