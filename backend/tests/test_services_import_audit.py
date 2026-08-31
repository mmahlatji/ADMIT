import uuid
from datetime import date

from app.queries.system_logs import get_system_logs
from app.services.imports.audit import record_change
from tests.test_queries_notes import _create_author

IMPORT_RUN_ID = uuid.uuid4()
CHANGED_BY = "9999999"
ENTITY_ID = uuid.uuid4()


def test_record_change_writes_nothing_when_nothing_changed(db_session):
    _create_author(db_session)

    record_change(
        db_session, "applicants", ENTITY_ID, CHANGED_BY, IMPORT_RUN_ID,
        old_data={"first_name": "Noah"}, new_data={"first_name": "Noah"},
    )

    assert get_system_logs(db_session) == []


def test_record_change_logs_only_the_changed_keys(db_session):
    _create_author(db_session)

    record_change(
        db_session, "applicants", ENTITY_ID, CHANGED_BY, IMPORT_RUN_ID,
        old_data={"first_name": "Noah", "last_name": "Smith"},
        new_data={"first_name": "Noah", "last_name": "Smyth"},
    )

    logs = get_system_logs(db_session)
    assert len(logs) == 1
    assert logs[0].old_data == {"last_name": "Smith"}
    assert logs[0].new_data == {"last_name": "Smyth"}


def test_record_change_serializes_dates_as_isoformat(db_session):
    _create_author(db_session)

    record_change(
        db_session, "applicants", ENTITY_ID, CHANGED_BY, IMPORT_RUN_ID,
        old_data={"birth_date": date(2000, 1, 1)},
        new_data={"birth_date": date(2000, 1, 2)},
    )

    logs = get_system_logs(db_session)
    assert logs[0].old_data == {"birth_date": "2000-01-01"}
    assert logs[0].new_data == {"birth_date": "2000-01-02"}
