
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicants import Applicant


class ApplicantRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, campus_id: str) -> Applicant | None:
            return self.session.get(Applicant, campus_id)

    def get_all(self) -> list[Applicant]:
        return list(
                    self.session.scalars(
                         select(Applicant)
                        ).all()
                    )

    def add(self, applicant: Applicant) -> None:
        self.session.add(applicant)
        self.session.commit()


    