import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notes import Note


def get_note_by_id(db: Session, note_id: uuid.UUID) -> Note | None:
    """Look up a note by its id. Returns None if it doesn't exist yet."""
    return db.execute(select(Note).where(Note.note_id == note_id)).scalar_one_or_none()


def get_notes(db: Session, skip: int = 0, limit: int = 100) -> list[Note]:
    """List notes, paginated."""
    return list(db.execute(select(Note).offset(skip).order_by(Note.created_at.desc()).limit(limit)).scalars())


def get_notes_by_campus_id(db: Session, campus_id: str) -> list[Note]:
    """List one applicant's notes, newest first"""
    return list(
        db.scalars(
            select(Note).where(
                Note.campus_id == campus_id
            ).order_by(Note.created_at.desc())
        )
    )


def create_note(db: Session, campus_id: str, author_id: str, content: str) -> Note:
    """Insert a new note row."""
    note = Note(
        note_id=uuid.uuid4(), campus_id=campus_id, author_id=author_id, content=content
    )
    db.add(note)
    db.flush()
    return note


def update_note( # why would you want to update a note ? Just make another one
    db: Session,
    note: Note,
    campus_id: str | None = None,
    author_id: str | None = None,
    content: str | None = None,
) -> Note:
    """Partially update a note, only sets fields explicitly passed."""
    fields = {"campus_id": campus_id, "author_id": author_id, "content": content}
    for field, value in fields.items():
        if value is not None:
            setattr(note, field, value)
    db.flush()
    return note


def delete_note(db: Session, note: Note) -> None:
    """Delete a note row."""
    db.delete(note)
    db.flush()
