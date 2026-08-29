from app.models.import_runs import ImportStatus, SourceType
from app.queries.import_runs import (
    create_import_run,
    delete_import_run,
    get_import_run_by_id,
    get_import_runs,
    update_import_run,
)
from tests.test_queries_notes import _create_author


def _create(db_session):
    _create_author(db_session)
    return create_import_run(
        db_session, SourceType.ASR, "9999999", "asr.xlsx", ImportStatus.PENDING, rows_total=10
    )


def test_create_and_get_import_run(db_session):
    import_run = _create(db_session)

    fetched = get_import_run_by_id(db_session, import_run.import_run_id)
    assert fetched is not None
    assert fetched.status == ImportStatus.PENDING
    assert fetched.rows_loaded == 0


def test_get_import_runs_returns_all(db_session):
    _create_author(db_session)
    create_import_run(db_session, SourceType.ASR, "9999999", "a.xlsx", ImportStatus.PENDING, 10)
    create_import_run(db_session, SourceType.UCT_MARKS, "9999999", "b.xlsx", ImportStatus.PENDING, 5)

    assert len(get_import_runs(db_session)) == 2


def test_update_import_run_only_sets_passed_fields(db_session):
    import_run = _create(db_session)

    updated = update_import_run(db_session, import_run, status=ImportStatus.COMPLETED, rows_loaded=10)
    assert updated.file_name == "asr.xlsx"
    assert updated.status == ImportStatus.COMPLETED
    assert updated.rows_loaded == 10


def test_delete_import_run(db_session):
    import_run = _create(db_session)

    delete_import_run(db_session, import_run)

    assert get_import_run_by_id(db_session, import_run.import_run_id) is None
