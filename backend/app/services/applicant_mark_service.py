
from app.models.applicant_marks import ApplicantMark
from app.queries.applicant_mark_repository import ApplicantMarkRepository
from app.schemas.applicant_marks import ApplicantMarkCreate


class ApplicantMarkService:
    def __init__(self, applicantMarkRepository: ApplicantMarkRepository) -> None:
        self.repository = applicantMarkRepository

    def get_by_id(self, mark_id: int) -> ApplicantMark | None:
        """
        Returns: One row from ApplicantMark table in the database
        """
        return self.repository.get_by_id(mark_id)
    

    def get_by_campus_id(self, campus_id: str) -> list[ApplicantMark]:
        """
        Returns: All available recorded marks for an applicant
        """
        return self.repository.get_by_campus_id(campus_id)

    def get_all(self) -> list[ApplicantMark]:
        return list(self.repository.get_all())

    def add(self, data: ApplicantMarkCreate) -> None:
        applicant_mark = ApplicantMark(**data.model_dump())
        self.repository.add(applicant_mark)