import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.motivations import Motivation


def get_motivation_by_id(db: Session, motivation_id: uuid.UUID) -> Motivation | None:
    """Look up a motivation by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(Motivation).where(Motivation.motivation_id == motivation_id)
    ).scalar_one_or_none()


def get_motivations(db: Session, skip: int = 0, limit: int = 100) -> list[Motivation]:
    """List motivations, paginated."""
    return list(db.execute(select(Motivation).offset(skip).order_by(Motivation.campus_id.asc()).limit(limit)).scalars())


def create_motivation(
    db: Session,
    campus_id: str,
    last_name: str,
    first_name: str,
    motivation: str | None = None,
) -> Motivation:
    """Insert a new motivation row."""
    motivation_row = Motivation(
        motivation_id=uuid.uuid4(),
        campus_id=campus_id,
        last_name=last_name,
        first_name=first_name,
        motivation=motivation,
    )
    db.add(motivation_row)
    db.flush()
    db.refresh(motivation_row)
    return motivation_row


def update_motivation(
    db: Session,
    motivation_row: Motivation,
    campus_id: str | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    motivation: str | None = None,
) -> Motivation:
    """Partially update a motivation, only sets fields explicitly passed."""
    fields = {
        "campus_id": campus_id,
        "last_name": last_name,
        "first_name": first_name,
        "motivation": motivation,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(motivation_row, field, value)
    db.flush()
    db.refresh(motivation_row)
    return motivation_row


def delete_motivation(db: Session, motivation_row: Motivation) -> None:
    """Delete a motivation row."""
    db.delete(motivation_row)
    db.flush()
