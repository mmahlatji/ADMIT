import uuid

from app.queries.import_documents import (
    create_import_document,
    delete_import_document,
    get_import_document_by_id,
    get_import_documents,
    update_import_document,
)
from tests.test_queries_import_runs import _create as create_import_run


def _create(db_session, sha256_hash="a" * 64):
    import_run = create_import_run(db_session)
    return create_import_document(
        db_session,
        import_run.import_run_id,
        uuid.uuid4(),
        "asr.xlsx",
        "application/vnd.ms-excel",
        sha256_hash,
    )


def test_create_and_get_import_document(db_session):
    document = _create(db_session)

    fetched = get_import_document_by_id(db_session, document.document_id)
    assert fetched is not None
    assert fetched.original_file_name == "asr.xlsx"


def test_get_import_documents_returns_all(db_session):
    import_run = create_import_run(db_session)
    create_import_document(
        db_session, import_run.import_run_id, uuid.uuid4(), "a.xlsx", "text/csv", "a" * 64
    )
    create_import_document(
        db_session, import_run.import_run_id, uuid.uuid4(), "b.xlsx", "text/csv", "b" * 64
    )

    assert len(get_import_documents(db_session)) == 2


def test_update_import_document_only_sets_passed_fields(db_session):
    document = _create(db_session)

    updated = update_import_document(db_session, document, original_file_name="renamed.xlsx")
    assert updated.original_file_name == "renamed.xlsx"
    assert updated.content_type == "application/vnd.ms-excel"


def test_delete_import_document(db_session):
    document = _create(db_session)

    delete_import_document(db_session, document)

    assert get_import_document_by_id(db_session, document.document_id) is None
