
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notes import Note


class NoteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        return self.session.get(Note, note_id)

    def get_all(self) -> list[Note]:
        return list(self.session.scalars(select(Note)).all())

    def add(self, note: Note) -> None:
        self.session.add(note)
        self.session.commit()

