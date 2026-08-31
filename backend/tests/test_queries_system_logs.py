import uuid

from app.models.system_logs import ChangeSource
from app.queries.system_logs import (
    create_system_log,
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

