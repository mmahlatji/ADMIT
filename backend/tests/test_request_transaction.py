"""Guards the transaction contract that get_db owns.

A request is one transaction: everything it writes lands together or not at
all. Two things used to break that quietly. Query modules committing on their
own put half a request beyond the reach of get_db's rollback, and the router
tests overrode get_db with a bare `yield session`, which commits and rolls
back nothing, so neither fault could fail a test.
"""

import uuid
from pathlib import Path

from app.models.users import RoleEnum, User
from app.queries.users import get_user_by_id
from app.services import users as users_service
from tests.test_notes_router import _make_actor, _make_client, _teardown

QUERIES_DIR = Path(__file__).resolve().parent.parent / "app" / "queries"


def test_no_query_module_commits_on_its_own():
    """get_db commits once per request. A query module that commits too puts
    everything written before it beyond the reach of get_db's rollback."""
    offenders = sorted(
        path.relative_to(QUERIES_DIR).as_posix()
        for path in QUERIES_DIR.rglob("*.py")
        if "db.commit()" in path.read_text(encoding="utf-8")
    )

    assert offenders == [], (
        "these query modules commit instead of flushing, which breaks the "
        f"one transaction per request that get_db provides: {offenders}"
    )


def test_a_failed_role_change_leaves_the_old_role(db_session, monkeypatch):
    """The role change and the log entry recording it are one unit.

    update_user_role used to commit on its own while the log entry only
    flushed, so a failure writing the log left a role changed with nothing
    saying who changed it.
    """
    actor = _make_actor(db_session, role=RoleEnum.convenor)
    target = User(
        user_id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@uct.ac.za",
        employee_id="1231231",
        role=None,
    )
    db_session.add(target)
    db_session.commit()

    def explode(*args, **kwargs):
        raise RuntimeError("writing the audit entry failed")

    monkeypatch.setattr(
        users_service.system_log_queries, "create_system_log", explode
    )

    client = _make_client(db_session, actor)
    try:
        # handle_unhandled_errors turns this into a 500 rather than letting it
        # escape, and the dependency teardown that rolls the request back has
        # already run by the time it does.
        response = client.post(
            f"/users/{target.user_id}/role", json={"role": "committee"}
        )
        assert response.status_code == 500
    finally:
        _teardown()

    assert get_user_by_id(db_session, target.user_id).role is None


def test_a_successful_request_keeps_what_it_wrote(db_session):
    """The other half of the contract: a request that succeeds persists."""
    actor = _make_actor(db_session, role=RoleEnum.convenor)
    target = User(
        user_id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@uct.ac.za",
        employee_id="3213213",
        role=None,
    )
    db_session.add(target)
    db_session.commit()

    client = _make_client(db_session, actor)
    try:
        response = client.post(
            f"/users/{target.user_id}/role", json={"role": "committee"}
        )
        assert response.status_code == 200
    finally:
        _teardown()

    assert get_user_by_id(db_session, target.user_id).role is RoleEnum.committee
