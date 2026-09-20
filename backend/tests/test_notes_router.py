import uuid

from fastapi.testclient import TestClient

from app.deps import get_current_user, get_db
from app.main import app
from app.models.users import RoleEnum, User
from app.services import notes as note_service
from tests.support import request_scoped_db
from tests.test_queries_applicants import _create as create_applicant


def _make_actor(db_session, role=RoleEnum.convenor, employee_id="9999999"):
    actor = User(
        user_id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@uct.ac.za",
        employee_id=employee_id,
        role=role,
    )
    db_session.add(actor)
    db_session.commit()
    return actor


def _make_client(db_session, actor):
    app.dependency_overrides[get_db] = request_scoped_db(db_session)
    if actor is not None:
        app.dependency_overrides[get_current_user] = lambda: actor
    else:
        app.dependency_overrides.pop(get_current_user, None)

    return TestClient(app)


def _teardown():
    app.dependency_overrides.clear()


def test_list_notes_returns_applicant_notes(db_session):
    create_applicant(db_session)
    actor = _make_actor(db_session)
    note_service.create_note(db_session, actor, "xxxyyy001", "Looks strong")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/notes", params={"campus_id": "xxxyyy001"})
        assert res.status_code == 200
        body = res.json()
        assert len(body) == 1
        assert body[0]["content"] == "Looks strong"
        assert body[0]["campus_id"] == "xxxyyy001"
        assert body[0]["author_id"] == "9999999"
    finally:
        _teardown()


def test_create_note(db_session):
    create_applicant(db_session)
    actor = _make_actor(db_session)

    client = _make_client(db_session, actor)
    try:
        res = client.post(
            "/notes",
            json={"campus_id": "xxxyyy001", "author_id": "9999999", "content": "Looks strong"},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["content"] == "Looks strong"
        assert body["campus_id"] == "xxxyyy001"
        assert "note_id" in body
    finally:
        _teardown()


def test_delete_note(db_session):
    create_applicant(db_session)
    actor = _make_actor(db_session)
    note = note_service.create_note(db_session, actor, "xxxyyy001", "Bye")

    client = _make_client(db_session, actor)
    try:
        res = client.delete(f"/notes/{note.note_id}")
        assert res.status_code == 204
        assert note_service.get_note_by_id(db_session, note.note_id) is None
    finally:
        _teardown()


def test_delete_note_not_found(db_session):
    actor = _make_actor(db_session)

    client = _make_client(db_session, actor)
    try:
        res = client.delete(f"/notes/{uuid.uuid4()}")
        assert res.status_code == 404
    finally:
        _teardown()


def test_list_notes_forbidden_for_unapproved_staff(db_session):
    actor = _make_actor(db_session, role=None)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/notes", params={"campus_id": "xxxyyy001"})
        assert res.status_code == 403
    finally:
        _teardown()


def test_create_note_requires_authentication(db_session):
    client = _make_client(db_session, actor=None)
    try:
        res = client.post(
            "/notes",
            json={"campus_id": "xxxyyy001", "author_id": "9999999", "content": "Hi"},
        )
        assert res.status_code == 401
    finally:
        _teardown()
