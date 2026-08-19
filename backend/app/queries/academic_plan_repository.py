import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicPlan


class AcademicPlanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, academic_plan_id: uuid.UUID) -> AcademicPlan | None:
        return self.session.get(AcademicPlan, academic_plan_id)

    def get_all(self) -> list[AcademicPlan]:
        return list(self.session.scalars(select(AcademicPlan)).all())

    def add(self, academic_plan: AcademicPlan) -> None:
        self.session.add(academic_plan)
        self.session.commit()

