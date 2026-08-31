import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.courses import Course


def get_course_by_id(db: Session, course_id: uuid.UUID) -> Course | None:
    """Look up a course by its id. Returns None if it doesn't exist yet."""
    return db.execute(select(Course).where(Course.course_id == course_id)).scalar_one_or_none()


def get_courses(db: Session, skip: int = 0, limit: int = 100) -> list[Course]:
    """List courses, paginated."""
    return list(db.execute(select(Course).offset(skip).order_by(Course.department_code.asc()).limit(limit)).scalars())


def create_course(
    db: Session, department_code: str, course_code: str, course_name: str | None = None
) -> Course:
    """Insert a new course row."""
    course = Course(
        course_id=uuid.uuid4(),
        department_code=department_code,
        course_code=course_code,
        course_name=course_name,
    )
    db.add(course)
    db.flush()
    return course


def update_course(
    db: Session,
    course: Course,
    department_code: str | None = None,
    course_code: str | None = None,
    course_name: str | None = None,
) -> Course:
    """Partially update a course, only sets fields explicitly passed."""
    fields = {
        "department_code": department_code,
        "course_code": course_code,
        "course_name": course_name,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(course, field, value)
    db.flush()
    return course


def delete_course(db: Session, course: Course) -> None:
    """Delete a course row."""
    db.delete(course)
    db.flush()
