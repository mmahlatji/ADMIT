
from app.models.academic_plans import AcademicPlan
from app.queries.academic_plan_repository import AcademicPlanRepository
from app.schemas.academic_plans import AcademicPlanCreate


class AcademicPlanService:
    def __init__(self, academicPlanRepository: AcademicPlanRepository) -> None:
        self.repository = academicPlanRepository

    def get_by_id(self, academic_plan_id: int) -> AcademicPlan | None:
        return self.repository.get_by_id(academic_plan_id)

    def get_all(self) -> list[AcademicPlan]:
        return list(self.repository.get_all())

    def add(self, data: AcademicPlanCreate) -> None:
        academic_plan = AcademicPlan(**data.model_dump())
        self.repository.add(academic_plan)
