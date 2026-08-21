
import uuid

from app.models.applicants import Applicant
from app.queries.applicant_repository import ApplicantRepository
from app.schemas.applicants import ApplicantCreate


class ApplicantService:
    def __init__(self, applicant_repository: ApplicantRepository) -> None:
        self.repository = applicant_repository

    def get_by_id(self, applicant_id: uuid.UUID) -> Applicant | None:
        return self.repository.get_by_id(applicant_id)

    def get_all(self) -> list[Applicant]:
        return list(self.repository.get_all())

    def add(self, data: ApplicantCreate) -> None:
        applicant = Applicant(**data.model_dump())
        self.repository.add(applicant)