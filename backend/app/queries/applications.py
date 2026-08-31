import uuid
from datetime import date

from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.models.applications import Application, ApplicationStatus, Choice, DenyReason, Semester


def get_active_applications_by_campus_ids(db: Session, campus_ids: list[str], application_date: date) -> list[Application]:
    """
        Look up applications by campus ids within the year given by application date, 
        returns an empty list if applications do not exist yet.
    """
    return list(db.scalars(
            select(Application).where(
                Application.campus_id.in_(campus_ids), 
                extract("year", Application.application_date) == application_date.year
            )).all()
    )

def get_application_by_id(db: Session, application_id: uuid.UUID) -> Application | None:
    """Look up an application by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(Application).where(Application.application_id == application_id)
    ).scalar_one_or_none()


def get_application_by_number(db: Session, application_number: str) -> Application | None:
    """Look up an application by its application number (its natural key across imports)."""
    return db.execute(
        select(Application).where(Application.application_number == application_number)
    ).scalar_one_or_none()



def get_applications(db: Session, skip: int = 0, limit: int = 100) -> list[Application]:
    """List applications, paginated."""
    return list(db.execute(select(Application).offset(skip).order_by(Application.campus_id.asc()).limit(limit)).scalars())


def list_applications(
    db: Session,
    campus_id: str | None = None,
    application_status: ApplicationStatus | None = None,
    application_number: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Application]:
    """List applications, optionally filtered by campus id, status or number."""
    stmt = select(Application)
    if campus_id is not None:
        stmt = stmt.where(Application.campus_id == campus_id)
    if application_status is not None:
        stmt = stmt.where(Application.application_status == application_status)
    if application_number is not None:
        stmt = stmt.where(Application.application_number == application_number)
    stmt = stmt.order_by(Application.campus_id.asc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars())


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
    application = Application(
        application_id=uuid.uuid4(),
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
    db.add(application)
    db.flush()
    db.refresh(application)
    return application


def update_application(
    db: Session,
    application: Application,
    application_number: str | None = None,
    campus_id: str | None = None,
    academic_program_code: str | None = None,
    academic_plan1: str | None = None,
    choice: Choice | None = None,
    application_status: ApplicationStatus | None = None,
    semester: Semester | None = None,
    application_date: date | None = None,
    effective_date: date | None = None,
    last_registration: str | None = None,
    previous_application_term: int | None = None,
    incorrect_plan: bool | None = None,
    duplicate_application: bool | None = None,
    application_status_reason: DenyReason | None = None,
    requires_plan_correction: bool | None = None,
) -> Application:
    """Partially update an application, only sets fields explicitly passed."""
    fields = {
        "application_number": application_number,
        "campus_id": campus_id,
        "academic_program_code": academic_program_code,
        "academic_plan1": academic_plan1,
        "choice": choice,
        "application_status": application_status,
        "semester": semester,
        "application_date": application_date,
        "effective_date": effective_date,
        "last_registration": last_registration,
        "previous_application_term": previous_application_term,
        "incorrect_plan": incorrect_plan,
        "duplicate_application": duplicate_application,
        "application_status_reason": application_status_reason,
        "requires_plan_correction": requires_plan_correction,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(application, field, value)
    db.flush()
    db.refresh(application)
    return application


def delete_application(db: Session, application: Application) -> None:
    """Delete an application row."""
    db.delete(application)
    db.flush()
