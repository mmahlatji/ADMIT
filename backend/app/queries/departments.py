import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.departments import Department


def get_department_by_id(db: Session, department_id: uuid.UUID) -> Department | None:
    """Look up a department by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(Department).where(Department.department_id == department_id)
    ).scalar_one_or_none()


def get_departments(db: Session, skip: int = 0, limit: int = 100) -> list[Department]:
    """List departments, paginated."""
    return list(db.execute(select(Department).offset(skip).order_by(Department.department_code.asc()).limit(limit)).scalars())


def create_department(
    db: Session, department_code: str, department_name: str | None = None
) -> Department:
    """Insert a new department row."""
    department = Department(
        department_id=uuid.uuid4(),
        department_code=department_code,
        department_name=department_name,
    )
    db.add(department)
    db.flush()
    return department


def update_department(
    db: Session,
    department: Department,
    department_code: str | None = None,
    department_name: str | None = None,
) -> Department:
    """Partially update a department, only sets fields explicitly passed."""
    fields = {"department_code": department_code, "department_name": department_name}
    for field, value in fields.items():
        if value is not None:
            setattr(department, field, value)
    db.flush()
    return department


def delete_department(db: Session, department: Department) -> None:
    """Delete a department row."""
    db.delete(department)
    db.flush()
