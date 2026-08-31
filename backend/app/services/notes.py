import uuid

from sqlalchemy.orm import Session

from app.models import User
from app.models.notes import Note
from app.queries import notes as note_queries


def list_notes_by_campus_id(db: Session, campus_id: str) -> list[Note]:
    return note_queries.get_notes_by_campus_id(db, campus_id)


def get_note_by_id(db: Session, note_id: uuid.UUID) -> Note | None:
    return note_queries.get_note_by_id(db, note_id)


def create_note(db: Session, actor: User, campus_id:str, content: str) -> Note:
    return note_queries.create_note(db, campus_id, actor.employee_id, content)

def delete_note(db: Session, note: Note) -> None:
    note_queries.delete_note(db, note)