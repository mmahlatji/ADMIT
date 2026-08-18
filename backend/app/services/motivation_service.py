
from app.models.motivations import Motivation
from app.queries.motivation_repository import MotivationRepository
from app.schemas.motivations import MotivationCreate


class MotivationService:
    def __init__(self, motivationRepository: MotivationRepository) -> None:
        self.repository = motivationRepository

    def get_by_id(self, campus_id: str) -> Motivation | None:
        return self.repository.get_by_id(campus_id)

    def get_all(self) -> list[Motivation]:
        return list(self.repository.get_all())

    def add(self, data: MotivationCreate) -> None:
        motivation = Motivation(**data.model_dump())
        self.repository.add(motivation)
