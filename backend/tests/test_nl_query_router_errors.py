"""The natural-language query endpoints must not echo SQL back to the client.

The executor deliberately keeps table and column names out of its error
messages, because a committee member's role restricts which tables they may
query at all. A SQLAlchemyError stringifies to the whole statement and its
bound parameters, so returning one undoes that in a single line.
"""

import uuid

import pytest
from sqlalchemy.exc import ProgrammingError

from app.models.users import RoleEnum
from app.services import nl_query as nl_query_service
from tests.test_notes_router import _make_actor, _make_client, _teardown

LEAKY = ProgrammingError(
    "SELECT applicants.campus_id, applicants.email FROM applicants",
    {"status": "Denied"},
    Exception("column applicants.nope does not exist"),
)


def test_the_statement_is_in_the_exception_we_are_guarding_against():
    """Pins the premise: if SQLAlchemy stops doing this, the guard is moot."""
    rendered = str(LEAKY)

    assert "SELECT applicants.campus_id" in rendered
    assert "parameters" in rendered


def test_ask_does_not_return_the_sql(db_session, monkeypatch):
    async def boom(*args, **kwargs):
        raise LEAKY

    monkeypatch.setattr(nl_query_service, "ask", boom)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.post("/api/query", json={"prompt": "how many applicants"})
        assert res.status_code == 500
        detail = res.json()["detail"]
        assert "SELECT" not in detail
        assert "applicants" not in detail
        assert "parameters" not in detail
    finally:
        _teardown()


def test_replaying_a_saved_query_does_not_return_the_sql(db_session, monkeypatch):
    def boom(*args, **kwargs):
        raise LEAKY

    monkeypatch.setattr(nl_query_service, "get_page", boom)
    actor = _make_actor(db_session, role=RoleEnum.committee)

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/api/query/{uuid.uuid4()}")
        assert res.status_code == 500
        detail = res.json()["detail"]
        assert "SELECT" not in detail
        assert "applicants" not in detail
    finally:
        _teardown()


@pytest.mark.parametrize("role", [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin])
def test_no_role_is_shown_the_sql(db_session, monkeypatch, role):
    async def boom(*args, **kwargs):
        raise LEAKY

    monkeypatch.setattr(nl_query_service, "ask", boom)
    actor = _make_actor(db_session, role=role)

    client = _make_client(db_session, actor)
    try:
        res = client.post("/api/query", json={"prompt": "anything"})
        assert "SELECT" not in res.json()["detail"]
    finally:
        _teardown()
