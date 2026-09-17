import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.applicants import Applicant, CitizenshipResidency, SexEnum, TitleEnum


def get_applicant_by_id(db: Session, applicant_id: uuid.UUID) -> Applicant | None:
    """Look up an applicant by their id. Returns None if they don't exist yet."""
    return db.execute(
        select(Applicant).where(Applicant.applicant_id == applicant_id)
    ).scalar_one_or_none()


def get_applicant_by_campus_id(db: Session, campus_id: str) -> Applicant | None:
    """Look up an applicant by their campus id (their natural key across imports)."""
    return db.execute(
        select(Applicant).where(Applicant.campus_id == campus_id)
    ).scalar_one_or_none()


def get_applicants_by_campus_ids(db: Session, campus_ids: list[str]) -> list[Applicant]:
    """Look up applicants by a list of campus ids. Returns an empty list if none exist."""
    return list(
        db.execute(
            select(Applicant)
            .where(Applicant.campus_id.in_(campus_ids))
            .order_by(Applicant.campus_id.asc())
        ).scalars()
    )


def get_applicant_by_campus_id_with_relations(
    db: Session, campus_id: str
) -> Applicant | None:
    """Look up an applicant by campus id, eager-loading their detail view."""
    return db.execute(
        select(Applicant)
        .options(
            selectinload(Applicant.applications),
            selectinload(Applicant.applicant_marks),
            selectinload(Applicant.motivation),
            selectinload(Applicant.notes),
        )
        .where(Applicant.campus_id == campus_id)
    ).scalar_one_or_none()


def get_applicants(db: Session, skip: int = 0, limit: int = 100) -> list[Applicant]:
    """List applicants, paginated."""
    # added orderby so each query is determisnistic
    return list(
        db.execute(
            select(Applicant)
            .offset(skip)
            .order_by(Applicant.campus_id.asc())
            .limit(limit)
        ).scalars()
    )


def create_applicant(
    db: Session,
    campus_id: str,
    employee_id: str,
    title: TitleEnum,
    first_name: str,
    last_name: str,
    citizenship_residency: CitizenshipResidency,
    sex: SexEnum | None = None,
    cell_phone: str | None = None,
    home_phone: str | None = None,
    email: str | None = None,
    population_group: str | None = None,
    birth_date: date | None = None,
    non_sa_citizenship: str | None = None,
) -> Applicant:
    """Insert a new applicant row."""
    applicant = Applicant(
        applicant_id=uuid.uuid4(),
        campus_id=campus_id,
        employee_id=employee_id,
        title=title,
        first_name=first_name,
        last_name=last_name,
        citizenship_residency=citizenship_residency,
        sex=sex,
        cell_phone=cell_phone,
        home_phone=home_phone,
        email=email,
        population_group=population_group,
        birth_date=birth_date,
        non_sa_citizenship=non_sa_citizenship,
    )
    db.add(applicant)
    db.flush()
    return applicant


def update_applicant(
    db: Session,
    applicant: Applicant,
    campus_id: str | None = None,
    employee_id: str | None = None,
    title: TitleEnum | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    citizenship_residency: CitizenshipResidency | None = None,
    sex: SexEnum | None = None,
    cell_phone: str | None = None,
    home_phone: str | None = None,
    email: str | None = None,
    population_group: str | None = None,
    birth_date: date | None = None,
    non_sa_citizenship: str | None = None,
) -> Applicant:
    """Partially update an applicant, only sets fields explicitly passed."""
    fields = {
        "campus_id": campus_id,
        "employee_id": employee_id,
        "title": title,
        "first_name": first_name,
        "last_name": last_name,
        "citizenship_residency": citizenship_residency,
        "sex": sex,
        "cell_phone": cell_phone,
        "home_phone": home_phone,
        "email": email,
        "population_group": population_group,
        "birth_date": birth_date,
        "non_sa_citizenship": non_sa_citizenship,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(applicant, field, value)
    db.flush()
    return applicant


def delete_applicant(db: Session, applicant: Applicant) -> None:
    """Delete an applicant row."""
    db.delete(applicant)
    db.flush()
