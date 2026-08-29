import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_applicants_data import ExternalApplicantData


def get_external_applicant_data_by_id(
    db: Session, ea_id: uuid.UUID
) -> ExternalApplicantData | None:
    """Look up external applicant data by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(ExternalApplicantData).where(ExternalApplicantData.ea_id == ea_id)
    ).scalar_one_or_none()


def get_external_applicants_data(
    db: Session, skip: int = 0, limit: int = 100
) -> list[ExternalApplicantData]:
    """List external applicant data rows, paginated."""
    return list(db.execute(select(ExternalApplicantData).offset(skip).order_by(ExternalApplicantData.application_number.asc()).limit(limit)).scalars())


def create_external_applicant_data(
    db: Session,
    application_number: str,
    missing_documents: str | None = None,
    prev_university_and_degree: str | None = None,
    correct_previous_degree: bool | None = None,
    degree_completed: bool | None = None,
    has_min_viable_marks: bool | None = None,
    comment: str | None = None,
) -> ExternalApplicantData:
    """Insert a new external applicant data row."""
    data = ExternalApplicantData(
        ea_id=uuid.uuid4(),
        application_number=application_number,
        missing_documents=missing_documents,
        prev_university_and_degree=prev_university_and_degree,
        correct_previous_degree=correct_previous_degree,
        degree_completed=degree_completed,
        has_min_viable_marks=has_min_viable_marks,
        comment=comment,
    )
    db.add(data)
    db.flush()
    db.refresh(data)
    return data


def update_external_applicant_data(
    db: Session,
    data: ExternalApplicantData,
    application_number: str | None = None,
    missing_documents: str | None = None,
    prev_university_and_degree: str | None = None,
    correct_previous_degree: bool | None = None,
    degree_completed: bool | None = None,
    has_min_viable_marks: bool | None = None,
    comment: str | None = None,
) -> ExternalApplicantData:
    """Partially update external applicant data, only sets fields explicitly passed."""
    fields = {
        "application_number": application_number,
        "missing_documents": missing_documents,
        "prev_university_and_degree": prev_university_and_degree,
        "correct_previous_degree": correct_previous_degree,
        "degree_completed": degree_completed,
        "has_min_viable_marks": has_min_viable_marks,
        "comment": comment,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(data, field, value)
    db.flush()
    db.refresh(data)
    return data


def delete_external_applicant_data(db: Session, data: ExternalApplicantData) -> None:
    """Delete an external applicant data row."""
    db.delete(data)
    db.flush()
