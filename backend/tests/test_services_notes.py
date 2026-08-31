import uuid

from app.models.users import User
from app.services import notes as note_service
from tests.test_queries_applicants import _create as create_applicant


def _create_author(db_session, employee_id="9999999"):
    author = User(user_id=uuid.uuid4(), email=f"{uuid.uuid4()}@uct.ac.za", employee_id=employee_id)
    db_session.add(author)
    db_session.commit()
    return author


def test_list_notes_by_campus_id_returns_only_that_applicant(db_session):
    create_applicant(db_session, "xxxyyy001", "1000001")
    create_applicant(db_session, "xxxyyy002", "1000002")
    author = _create_author(db_session)
    note_service.create_note(db_session, author, "xxxyyy001", "First")
    note_service.create_note(db_session, author, "xxxyyy002", "Other")

    notes = note_service.list_notes_by_campus_id(db_session, "xxxyyy001")

    assert len(notes) == 1
    assert notes[0].content == "First"


def test_list_notes_by_campus_id_returns_empty_for_unknown_campus(db_session):
    create_applicant(db_session)
    author = _create_author(db_session)
    note_service.create_note(db_session, author, "xxxyyy001", "First")

    assert note_service.list_notes_by_campus_id(db_session, "zzzyyy001") == []


def test_get_note_by_id(db_session):
    create_applicant(db_session)
    author = _create_author(db_session)
    note = note_service.create_note(db_session, author, "xxxyyy001", "Hi")

    assert note_service.get_note_by_id(db_session, note.note_id).content == "Hi"
    assert note_service.get_note_by_id(db_session, uuid.uuid4()) is None


def test_delete_note(db_session):
    create_applicant(db_session)
    author = _create_author(db_session)
    note = note_service.create_note(db_session, author, "xxxyyy001", "Bye")

    note_service.delete_note(db_session, note)

    assert note_service.get_note_by_id(db_session, note.note_id) is None
