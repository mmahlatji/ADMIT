
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, employee_id: str) -> User | None:
        return self.session.get(User, employee_id)

    def get_all(self) -> list[User]:
        return list(self.session.scalars(select(User)).all())

    def add(self, user: User) -> None:
        self.session.add(user)
        self.session.commit()

