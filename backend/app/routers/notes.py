import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.notes import NoteCreate, NoteResponse
from app.services import notes as note_service

router = APIRouter(prefix="/notes", tags=["notes"])


ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]

@router.get("", response_model=list[NoteResponse])
def list_notes(
    campus_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES))
):
    """List all the notes for an applicant"""
    return note_service.list_notes_by_campus_id(db, campus_id)



@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    body: NoteCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*ALLOWED_ROLES))
):
    """Create a note."""
    try:
        return note_service.create_note(db, actor, body.campus_id, body.content)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    # was get_current_user, which only proves the token is valid: a signed-up
    # user still awaiting approval (role is None) could delete anyone's note
    actor: User = Depends(require_role(*ALLOWED_ROLES))
):
    note = note_service.get_note_by_id(db, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
    # a note is the author's own record of their reasoning, so nobody else
    # gets to remove it, convenor included
    if note.author_id != actor.employee_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own notes")
    note_service.delete_note(db, note)