from app.models.staging import ValidationStatus
from app.queries.staging import (
    create_staging_row,
    delete_staging_row,
    get_staging_by_id,
    get_staging_rows,
    update_staging_row,
)
from tests.test_queries_import_runs import _create as create_import_run


def _create(db_session):
    import_run = create_import_run(db_session)
    return create_staging_row(
        db_session,
        import_run.import_run_id,
        "applicants",
        {"name": "Noah"},
        {"first_name": "Noah"},
        ValidationStatus.PENDING,
    )


def test_create_and_get_staging_row(db_session):
    staging = _create(db_session)

    fetched = get_staging_by_id(db_session, staging.staging_id)
    assert fetched is not None
    assert fetched.raw_data == {"name": "Noah"}
    assert fetched.validation_status == ValidationStatus.PENDING


def test_get_staging_rows_returns_all(db_session):
    import_run = create_import_run(db_session)
    create_staging_row(
        db_session, import_run.import_run_id, "applicants", {}, {}, ValidationStatus.PENDING
    )
    create_staging_row(
        db_session, import_run.import_run_id, "applicants", {}, {}, ValidationStatus.VALID
    )

    assert len(get_staging_rows(db_session)) == 2


def test_update_staging_row_only_sets_passed_fields(db_session):
    staging = _create(db_session)

    updated = update_staging_row(db_session, staging, validation_status=ValidationStatus.REJECTED)
    assert updated.entity == "applicants"
    assert updated.validation_status == ValidationStatus.REJECTED


def test_delete_staging_row(db_session):
    staging = _create(db_session)

    delete_staging_row(db_session, staging)

    assert get_staging_by_id(db_session, staging.staging_id) is None
