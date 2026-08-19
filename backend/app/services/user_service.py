
import uuid

from app.models.users import User
from app.queries.user_repository import UserRepository
from app.schemas.users import UserCreate


class UserService:
    def __init__(self, userRepository: UserRepository) -> None:
        self.repository = userRepository

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.repository.get_by_id(user_id)

    def get_all(self) -> list[User]:
        return list(self.repository.get_all())

    def add(self, data: UserCreate) -> None:
        user = User(**data.model_dump())
        self.repository.add(user)
