import uuid

from app.models.users import RoleEnum
from tests.test_notes_router import _make_actor, _make_client, _teardown
from tests.test_queries_applications import _create as create_application


def test_list_applications(db_session):
    create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/applications")
        assert res.status_code == 200
        assert len(res.json()) == 1
    finally:
        _teardown()


def test_list_applications_filter_by_status(db_session):
    create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/applications", params={"application_status": "Applied"})
        assert res.status_code == 200
        assert len(res.json()) == 1
        res = client.get("/applications", params={"application_status": "Denied"})
        assert res.json() == []
    finally:
        _teardown()


def test_get_application_by_id(db_session):
    application = create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/applications/{application.application_id}")
        assert res.status_code == 200
        assert res.json()["application_number"] == "00000001"
    finally:
        _teardown()


def test_get_application_not_found(db_session):
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/applications/{uuid.uuid4()}")
        assert res.status_code == 404
    finally:
        _teardown()


def test_transition_status_denies_with_reason(db_session):
    application = create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.convenor)

    client = _make_client(db_session, actor)
    try:
        res = client.post(
            f"/applications/{application.application_id}/status",
            json={"status": "Denied", "reason": "Not competitive"},
        )
        assert res.status_code == 200
        assert res.json()["application_status"] == "Denied"
        assert res.json()["application_status_reason"] == "Not competitive"
    finally:
        _teardown()


def test_transition_status_deny_requires_reason(db_session):
    application = create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.convenor)

    client = _make_client(db_session, actor)
    try:
        res = client.post(
            f"/applications/{application.application_id}/status", json={"status": "Denied"}
        )
        assert res.status_code == 400
    finally:
        _teardown()


def test_list_applications_forbidden_for_unapproved_staff(db_session):
    actor = _make_actor(db_session, role=None)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/applications")
        assert res.status_code == 403
    finally:
        _teardown()
