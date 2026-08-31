import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicant_marks import ApplicantMark, ResultCode


def get_applicant_mark_by_id(db: Session, mark_id: uuid.UUID) -> ApplicantMark | None:
    """Look up an applicant mark by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(ApplicantMark).where(ApplicantMark.mark_id == mark_id)
    ).scalar_one_or_none()


def get_applicant_mark_by_campus_and_course(
    db: Session, campus_id: str, course_code: str
) -> ApplicantMark | None:
    """Look up the mark for one applicant's course (their natural key, see the
    uq_applicant_marks_campus_id_course_code constraint on the model)."""
    return db.execute(
        select(ApplicantMark).where(
            ApplicantMark.campus_id == campus_id, ApplicantMark.course_code == course_code
        )
    ).scalar_one_or_none()



def get_applicant_marks(db: Session, skip: int = 0, limit: int = 100) -> list[ApplicantMark]:
    """List applicant marks, paginated."""
    return list(db.execute(select(ApplicantMark).offset(skip).order_by(ApplicantMark.campus_id.asc()).limit(limit)).scalars())


def create_applicant_mark(
    db: Session, campus_id: str, course_code: str, mark: int, result_code: ResultCode
) -> ApplicantMark:
    """Insert a new applicant mark row."""
    applicant_mark = ApplicantMark(
        mark_id=uuid.uuid4(), campus_id=campus_id, course_code=course_code, mark=mark, result_code=result_code
    )
    db.add(applicant_mark)
    db.flush()
    return applicant_mark


def update_applicant_mark(
    db: Session,
    applicant_mark: ApplicantMark,
    campus_id: str | None = None,
    course_code: str | None = None,
    mark: int | None = None,
    result_code: ResultCode | None = None,
) -> ApplicantMark:
    """Partially update an applicant mark, only sets fields explicitly passed."""
    fields = {"campus_id": campus_id, "course_code": course_code, "mark": mark, "result_code": result_code}
    for field, value in fields.items():
        if value is not None:
            setattr(applicant_mark, field, value)
    db.flush()
    return applicant_mark


def delete_applicant_mark(db: Session, applicant_mark: ApplicantMark) -> None:
    """Delete an applicant mark row."""
    db.delete(applicant_mark)
    db.flush()
