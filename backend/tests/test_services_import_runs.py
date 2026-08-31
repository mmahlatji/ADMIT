import pytest

from app.models.import_runs import ImportStatus, SourceType
from app.services import import_runs as service
from tests.test_queries_notes import _create_author


def test_create_import_run_rejects_blank_uploaded_by(db_session):
    _create_author(db_session)

    with pytest.raises(ValueError):
        service.create_import_run(
            db_session,
            source_type=SourceType.ASR,
            uploaded_by="   ",
            file_name="asr.xlsx",
            status=ImportStatus.PROCESSING,
            rows_total=1,
        )


def test_create_import_run_creates_with_defaults(db_session):
    _create_author(db_session)

    run = service.create_import_run(
        db_session,
        source_type=SourceType.ASR,
        uploaded_by="9999999",
        file_name="asr.xlsx",
        status=ImportStatus.PROCESSING,
        rows_total=10,
    )

    assert run.file_name == "asr.xlsx"
    assert run.rows_total == 10
    assert run.rows_loaded == 0
    assert run.rows_rejected == 0
    assert run.status == ImportStatus.PROCESSING


def test_update_import_run_only_sets_passed_fields(db_session):
    _create_author(db_session)
    run = service.create_import_run(
        db_session,
        source_type=SourceType.ASR,
        uploaded_by="9999999",
        file_name="asr.xlsx",
        status=ImportStatus.PROCESSING,
        rows_total=10,
    )

    updated = service.update_import_run(db_session, run, status=ImportStatus.COMPLETED, rows_loaded=7)

    assert updated.status == ImportStatus.COMPLETED
    assert updated.rows_loaded == 7
    assert updated.file_name == "asr.xlsx"
    assert updated.rows_total == 10
