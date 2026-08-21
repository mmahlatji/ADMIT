
import uuid

from app.models.motivations import Motivation
from app.queries.motivation_repository import MotivationRepository
from app.schemas.motivations import MotivationCreate


class MotivationService:
    def __init__(self, motivation_repository: MotivationRepository) -> None:
        self.repository = motivation_repository

    def get_by_id(self, motivation_id: uuid.UUID) -> Motivation | None:
        return self.repository.get_by_id(motivation_id)

    def get_all(self) -> list[Motivation]:
        return list(self.repository.get_all())

    def add(self, data: MotivationCreate) -> None:
        motivation = Motivation(**data.model_dump())
        self.repository.add(motivation)
