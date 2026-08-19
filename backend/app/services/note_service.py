
import uuid

from app.models.notes import Note
from app.queries.note_repository import NoteRepository
from app.schemas.notes import NoteCreate


class NoteService:
    def __init__(self, noteRepository: NoteRepository) -> None:
        self.repository = noteRepository

    def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        return self.repository.get_by_id(note_id)

    def get_all(self) -> list[Note]:
        return list(self.repository.get_all())

    def add(self, data: NoteCreate) -> None:
        note = Note(**data.model_dump())
        self.repository.add(note)
