import uuid

from app.models.users import User
from app.queries.notes import create_note, delete_note, get_note_by_id, get_notes, update_note
from tests.test_queries_applicants import _create as create_applicant


def _create_author(db_session, employee_id="9999999"):
    author = User(user_id=uuid.uuid4(), email="staff@uct.ac.za", employee_id=employee_id)
    db_session.add(author)
    db_session.commit()
    return author


def test_create_and_get_note(db_session):
    create_applicant(db_session)
    _create_author(db_session)
    note = create_note(db_session, "xxxyyy001", "9999999", "Looks strong")

    fetched = get_note_by_id(db_session, note.note_id)
    assert fetched is not None
    assert fetched.content == "Looks strong"


def test_get_notes_returns_all(db_session):
    create_applicant(db_session)
    _create_author(db_session)
    create_note(db_session, "xxxyyy001", "9999999", "First note")
    create_note(db_session, "xxxyyy001", "9999999", "Second note")

    assert len(get_notes(db_session)) == 2


def test_update_note_only_sets_passed_fields(db_session):
    create_applicant(db_session)
    _create_author(db_session)
    note = create_note(db_session, "xxxyyy001", "9999999", "Original")

    updated = update_note(db_session, note, content="Updated")
    assert updated.campus_id == "xxxyyy001"
    assert updated.content == "Updated"


def test_delete_note(db_session):
    create_applicant(db_session)
    _create_author(db_session)
    note = create_note(db_session, "xxxyyy001", "9999999", "Note")

    delete_note(db_session, note)

    assert get_note_by_id(db_session, note.note_id) is None
