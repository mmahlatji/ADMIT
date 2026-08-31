from app.models.users import RoleEnum
from tests.test_notes_router import _make_actor, _make_client, _teardown
from tests.test_queries_matching_reviews import _create as create_review


def test_list_reviews(db_session):
    create_review(db_session)
    actor = _make_actor(db_session, role=RoleEnum.convenor, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/matching_reviews")
        assert res.status_code == 200
        assert len(res.json()) == 1
    finally:
        _teardown()


def test_list_reviews_filter_by_status(db_session):
    create_review(db_session)
    actor = _make_actor(db_session, role=RoleEnum.convenor, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.get("/matching_reviews", params={"status": "pending"})
        assert res.status_code == 200
        assert len(res.json()) == 1
        res = client.get("/matching_reviews", params={"status": "resolved"})
        assert res.json() == []
    finally:
        _teardown()


def test_resolve_review(db_session):
    review = create_review(db_session)
    actor = _make_actor(db_session, role=RoleEnum.convenor, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.post(
            f"/matching_reviews/{review.match_id}/resolve", json={"resolution": "merge"}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "resolved"
        assert body["resolution"] == "merge"
    finally:
        _teardown()


def test_resolve_review_forbidden_for_committee(db_session):
    review = create_review(db_session)
    actor = _make_actor(db_session, role=RoleEnum.committee, employee_id="8888888")

    client = _make_client(db_session, actor)
    try:
        res = client.post(
            f"/matching_reviews/{review.match_id}/resolve", json={"resolution": "merge"}
        )
        assert res.status_code == 403
    finally:
        _teardown()
