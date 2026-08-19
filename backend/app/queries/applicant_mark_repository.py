
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicant_marks import ApplicantMark


class ApplicantMarkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, mark_id: uuid.UUID) -> ApplicantMark | None:
        return self.session.get(ApplicantMark, mark_id)

    def get_by_campus_id(self, campus_id: str) -> list[ApplicantMark]:
        return list(self.session.scalars(select(ApplicantMark).where(ApplicantMark.campus_id == campus_id)).all())

    def get_all(self) -> list[ApplicantMark]:
        return list(self.session.scalars(select(ApplicantMark)).all())

    def add(self, applicant_mark: ApplicantMark) -> None:
        self.session.add(applicant_mark)
        self.session.commit()
