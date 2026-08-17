from extensions import db
from auth.models import User


class UserRepository:
    def find_by_email(self, email: str) -> User | None:
        return db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()

    def find_by_username(self, username: str) -> User | None:
        return db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

    def save(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def find_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)
