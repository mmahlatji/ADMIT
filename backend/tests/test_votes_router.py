from app.models.users import RoleEnum
from app.models.votes import VoteDecision
from app.services import votes as votes_service
from tests.test_notes_router import _make_actor, _make_client, _teardown
from tests.test_queries_applications import _create as create_application


def test_create_vote(db_session):
    create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.post("/votes", json={"application_number": "00000001", "vote": "yes"})
        assert res.status_code == 201
        body = res.json()
        assert body["vote"] == "yes"
        assert body["voter_id"] == "9999999"
        assert body["campus_id"] == "xxxyyy001"
    finally:
        _teardown()


def test_create_vote_requires_existing_application(db_session):
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.post("/votes", json={"application_number": "doesnotexist", "vote": "yes"})
        assert res.status_code == 404
    finally:
        _teardown()


def test_list_votes_for_application(db_session):
    create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)
    votes_service.create_vote(db_session, actor, "00000001", VoteDecision.YES)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/votes", params={"application_number": "00000001"})
        assert res.status_code == 200
        assert len(res.json()) == 1
    finally:
        _teardown()


def test_list_votes_forbidden_for_unapproved_staff(db_session):
    actor = _make_actor(db_session, role=None)

    client = _make_client(db_session, actor)
    try:
        res = client.get("/votes", params={"application_number": "00000001"})
        assert res.status_code == 403
    finally:
        _teardown()


def test_recasting_replaces_your_own_vote(db_session):
    create_application(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        client.post("/votes", json={"application_number": "00000001", "vote": "no"})
        res = client.post(
            "/votes", json={"application_number": "00000001", "vote": "yes"}
        )
        assert res.status_code == 201
        assert res.json()["vote"] == "yes"

        listed = client.get("/votes", params={"application_number": "00000001"})
        assert [v["vote"] for v in listed.json()] == ["yes"]
    finally:
        _teardown()

