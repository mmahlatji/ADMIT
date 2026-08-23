import uuid

from fastapi.testclient import TestClient

from app.deps import get_current_user, get_db
from app.main import app
from app.models.users import RoleEnum, User
from app.queries.users import create_user


def _create(db_session, email: str) -> User:
    return create_user(db_session, uuid.uuid4(), email, "Test", "User")


def _make_client(db_session, actor: User | None):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    if actor is not None:
        app.dependency_overrides[get_current_user] = lambda: actor
    else:
        app.dependency_overrides.pop(get_current_user, None)

    client = TestClient(app)
    return client


def _teardown():
    app.dependency_overrides.clear()


def test_me_returns_current_user(db_session):
    actor = _create(db_session, "convenor@uct.ac.za")
    client = _make_client(db_session, actor)
    try:
        res = client.get("/users/me")
        assert res.status_code == 200
        assert res.json()["user_id"] == str(actor.user_id)
    finally:
        _teardown()


def test_assign_role_allowed_for_convenor(db_session):
    actor = _create(db_session, "convenor@uct.ac.za")
    actor.role = RoleEnum.convenor
    target = _create(db_session, "newperson@uct.ac.za")

    client = _make_client(db_session, actor)
    try:
        res = client.post(f"/users/{target.user_id}/role", json={"role": "committee"})
        assert res.status_code == 200
        assert res.json()["role"] == "committee"
    finally:
        _teardown()


def test_assign_role_forbidden_for_committee(db_session):
    actor = _create(db_session, "committee@uct.ac.za")
    actor.role = RoleEnum.committee
    target = _create(db_session, "newperson@uct.ac.za")

    client = _make_client(db_session, actor)
    try:
        res = client.post(f"/users/{target.user_id}/role", json={"role": "committee"})
        assert res.status_code == 403
    finally:
        _teardown()


def test_assign_role_forbidden_for_admin(db_session):
    actor = _create(db_session, "admin@uct.ac.za")
    actor.role = RoleEnum.admin
    target = _create(db_session, "newperson@uct.ac.za")

    client = _make_client(db_session, actor)
    try:
        res = client.post(f"/users/{target.user_id}/role", json={"role": "committee"})
        assert res.status_code == 403
    finally:
        _teardown()


def test_assign_role_requires_authentication(db_session):
    target = _create(db_session, "newperson@uct.ac.za")

    client = _make_client(db_session, actor=None)
    try:
        res = client.post(f"/users/{target.user_id}/role", json={"role": "committee"})
        assert res.status_code == 401
    finally:
        _teardown()


def test_assign_role_supports_revoke(db_session):
    actor = _create(db_session, "convenor@uct.ac.za")
    actor.role = RoleEnum.convenor
    target = _create(db_session, "leaving@uct.ac.za")
    target.role = RoleEnum.committee

    client = _make_client(db_session, actor)
    try:
        res = client.post(f"/users/{target.user_id}/role", json={"role": None})
        assert res.status_code == 200
        assert res.json()["role"] is None
    finally:
        _teardown()
