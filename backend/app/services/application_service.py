
import uuid

from app.models.applications import AcademicCareer, Application, Choice, Semester
from app.queries.application_repository import ApplicationRepository
from app.schemas.applications import ApplicationCreate


class ApplicationService:
    def __init__(self, applicationRepository: ApplicationRepository) -> None:
        self.repository = applicationRepository

    def get_by_id(self, application_id: uuid.UUID) -> Application | None:
        return self.repository.get_by_id(application_id)

    def get_all(self) -> list[Application]:
        return list(self.repository.get_all())

    def add(self, data: ApplicationCreate) -> None:
        application = Application(
            application_number=data.application_number,
            campus_id=data.campus_id,
            academic_program_code=data.academic_program_code,
            academic_plan1=data.academic_plan1,
            academic_plan2=data.academic_plan2,
            academic_career=AcademicCareer(data.academic_career),
            application_date=data.application_date,
            choice=Choice(data.choice),
            admit_type=data.admit_type,
            semester=Semester(data.semester),
            last_registration=data.last_registration,
            application_term=data.application_term,
            previous_application_term=data.previous_application_term,
        )
        self.repository.add(application)
