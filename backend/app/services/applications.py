from datetime import date

from sqlalchemy.orm import Session

from app.models.applications import Application, ApplicationStatus, Choice, DenyReason, Semester
from app.queries import applications as appl_queries


def get_active_applications_by_campus_ids(db: Session, campus_ids: list[str], application_date: date) -> list[Application]:
    return appl_queries.get_active_applications_by_campus_ids(db, campus_ids, application_date)




def create_application(
    db: Session,
    application_number: str,
    campus_id: str,
    academic_program_code: str,
    academic_plan1: str,
    choice: Choice,
    application_status: ApplicationStatus,
    application_date: date,
    effective_date: date,
    semester: Semester | None = None,
    last_registration: str | None = None,
    previous_application_term: int | None = None,
    incorrect_plan: bool = False,
    duplicate_application: bool = False,
    application_status_reason: DenyReason | None = None,
    requires_plan_correction: bool = False,
) -> Application:
    """Insert a new application row."""
    application = appl_queries.create_application(
        db,
        application_number=application_number,
        campus_id=campus_id,
        academic_program_code=academic_program_code,
        academic_plan1=academic_plan1,
        choice=choice,
        application_status=application_status,
        semester=semester,
        application_date=application_date,
        effective_date=effective_date,
        last_registration=last_registration,
        previous_application_term=previous_application_term,
        incorrect_plan=incorrect_plan,
        duplicate_application=duplicate_application,
        application_status_reason=application_status_reason,
        requires_plan_correction=requires_plan_correction,
    )
    return application
