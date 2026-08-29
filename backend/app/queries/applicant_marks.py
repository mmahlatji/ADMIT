import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicant_marks import ApplicantMark


def get_applicant_mark_by_id(db: Session, mark_id: uuid.UUID) -> ApplicantMark | None:
    """Look up an applicant mark by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(ApplicantMark).where(ApplicantMark.mark_id == mark_id)
    ).scalar_one_or_none()


def get_applicant_marks(db: Session, skip: int = 0, limit: int = 100) -> list[ApplicantMark]:
    """List applicant marks, paginated."""
    return list(db.execute(select(ApplicantMark).offset(skip).order_by(ApplicantMark.campus_id.asc()).limit(limit)).scalars())


def create_applicant_mark(
    db: Session, campus_id: str, course_code: str, mark: str
) -> ApplicantMark:
    """Insert a new applicant mark row."""
    applicant_mark = ApplicantMark(
        mark_id=uuid.uuid4(), campus_id=campus_id, course_code=course_code, mark=mark
    )
    db.add(applicant_mark)
    db.flush()
    db.refresh(applicant_mark)
    return applicant_mark


def update_applicant_mark(
    db: Session,
    applicant_mark: ApplicantMark,
    campus_id: str | None = None,
    course_code: str | None = None,
    mark: str | None = None,
) -> ApplicantMark:
    """Partially update an applicant mark, only sets fields explicitly passed."""
    fields = {"campus_id": campus_id, "course_code": course_code, "mark": mark}
    for field, value in fields.items():
        if value is not None:
            setattr(applicant_mark, field, value)
    db.flush()
    db.refresh(applicant_mark)
    return applicant_mark


def delete_applicant_mark(db: Session, applicant_mark: ApplicantMark) -> None:
    """Delete an applicant mark row."""
    db.delete(applicant_mark)
    db.flush()
