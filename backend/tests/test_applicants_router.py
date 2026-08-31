from app.models.users import RoleEnum
from tests.test_notes_router import _make_actor, _make_client, _teardown
from tests.test_queries_applicants import _create as create_applicant


def test_list_applicants(db_session):
    create_applicant(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/applicants")
        assert res.status_code == 200
        assert len(res.json()) == 1
    finally:
        _teardown()


def test_get_applicant_detail(db_session):
    create_applicant(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/applicants/xxxyyy001")
        assert res.status_code == 200
        body = res.json()
        assert body["campus_id"] == "xxxyyy001"
        assert body["applications"] == []
        assert body["applicant_marks"] == []
        assert body["notes"] == []
        assert body["motivation"] is None
    finally:
        _teardown()


def test_get_applicant_not_found(db_session):
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/applicants/doesnotexist")
        assert res.status_code == 404
    finally:
        _teardown()
