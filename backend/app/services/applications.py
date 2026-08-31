import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.applications import Application, ApplicationStatus, Choice, DenyReason, Semester
from app.models.system_logs import ChangeSource
from app.queries import applications as appl_queries
from app.queries import system_logs as system_log_queries


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


def list_applications(
    db: Session,
    campus_id: str | None = None,
    application_status: ApplicationStatus | None = None,
    application_number: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Application]:
    return appl_queries.list_applications(
        db, campus_id, application_status, application_number, skip, limit
    )


def get_application_by_id(db: Session, application_id: uuid.UUID) -> Application | None:
    return appl_queries.get_application_by_id(db, application_id)


def transition_status(
    db: Session,
    actor,
    application: Application,
    status: ApplicationStatus,
    reason: DenyReason | None = None,
) -> Application:
    """Manually change an application's status, recording the decision."""
    if status == ApplicationStatus.DENIED and reason is None:
        raise ValueError("Denying an application requires a reason")
    if actor.employee_id is None:
        raise ValueError("Cannot transition an application without an employee id")
    old_status = application.application_status
    application = appl_queries.update_application(
        db,
        application,
        application_status=status,
        application_status_reason=reason,
    )
    system_log_queries.create_system_log(
        db,
        entity_name="applications",
        entity_id=application.application_id,
        changed_by=actor.employee_id,
        reason=ChangeSource.DECISION,
        old_data={"application_status": old_status},
        new_data={"application_status": status, "application_status_reason": reason},
    )
    return application
