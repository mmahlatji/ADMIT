import uuid
from datetime import UTC, datetime

from app.models.system_logs import ChangeSource
from app.queries.system_logs import (
    create_system_log,
    get_latest_system_log_by_entity_and_entity_id,
    get_system_log_by_id,
    get_system_logs,
    update_system_log,
)
from tests.test_queries_notes import _create_author


def _create(db_session):
    _create_author(db_session)
    return create_system_log(
        db_session,
        entity_name="applicant_marks",
        entity_id=uuid.uuid4(),
        changed_by="9999999",
        reason=ChangeSource.MANUAL_EDIT,
        old_data={"mark": "70"},
        new_data={"mark": "80"},
    )


def test_create_and_get_system_log(db_session):
    log = _create(db_session)

    fetched = get_system_log_by_id(db_session, log.log_id)
    assert fetched is not None
    assert fetched.reason == ChangeSource.MANUAL_EDIT
    assert fetched.new_data == {"mark": "80"}


def test_get_system_logs_returns_all(db_session):
    _create_author(db_session)
    create_system_log(
        db_session,
        entity_name="applicants",
        entity_id=uuid.uuid4(),
        changed_by="9999999",
        reason=ChangeSource.IMPORT,
    )
    create_system_log(
        db_session,
        entity_name="applications",
        entity_id=uuid.uuid4(),
        changed_by="9999999",
        reason=ChangeSource.IMPORT,
    )

    assert len(get_system_logs(db_session)) == 2


def test_update_system_log_only_sets_passed_fields(db_session):
    log = _create(db_session)

    updated = update_system_log(db_session, log, reason=ChangeSource.DECISION)
    assert updated.entity_name == "applicant_marks"
    assert updated.reason == ChangeSource.DECISION



def test_get_latest_system_log_returns_none_when_no_logs(db_session):
    _create_author(db_session)

    assert (
        get_latest_system_log_by_entity_and_entity_id(db_session, "applicant_marks", uuid.uuid4())
        is None
    )


def test_get_latest_system_log_returns_sole_log(db_session):
    log = _create(db_session)

    found = get_latest_system_log_by_entity_and_entity_id(
        db_session, "applicant_marks", log.entity_id
    )
    assert found is not None
    assert found.log_id == log.log_id


def test_get_latest_system_log_returns_most_recent(db_session):
    _create_author(db_session)
    entity_id = uuid.uuid4()
    older = create_system_log(
        db_session,
        entity_name="applicant_marks",
        entity_id=entity_id,
        changed_by="9999999",
        reason=ChangeSource.IMPORT,
    )
    newer = create_system_log(
        db_session,
        entity_name="applicant_marks",
        entity_id=entity_id,
        changed_by="9999999",
        reason=ChangeSource.MANUAL_EDIT,
    )
    # SQLite's CURRENT_TIMESTAMP is second-granular, so force a clear ordering
    older.changed_at = datetime(2026, 1, 1, tzinfo=UTC)
    newer.changed_at = datetime(2026, 1, 2, tzinfo=UTC)
    db_session.flush()

    found = get_latest_system_log_by_entity_and_entity_id(db_session, "applicant_marks", entity_id)
    assert found is not None
    assert found.log_id == newer.log_id



def test_paging_system_logs_is_stable_across_identical_timestamps(db_session):
    # One import writes many log rows in the same instant, so changed_at ties
    # are the normal case here rather than an edge one.
    _create_author(db_session)
    stamp = datetime(2026, 9, 18, 10, 0, tzinfo=UTC)
    for _ in range(6):
        log = create_system_log(
            db_session,
            entity_name="applicant_marks",
            entity_id=uuid.uuid4(),
            changed_by="9999999",
            reason=ChangeSource.IMPORT,
        )
        log.changed_at = stamp
    db_session.flush()

    seen = []
    for skip in (0, 2, 4):
        seen.extend(log.log_id for log in get_system_logs(db_session, skip=skip, limit=2))

    assert len(seen) == 6
    assert len(set(seen)) == 6
