import uuid

from app.models.import_runs import ImportStatus, SourceType
from app.queries.import_documents import (
    create_import_document,
    delete_import_document,
    get_import_document_by_id,
    get_import_documents,
    get_import_documents_by_hash,
    get_import_documents_by_run,
    update_import_document,
)
from app.queries.import_runs import create_import_run as make_import_run
from tests.test_queries_import_runs import _create as create_import_run
from tests.test_queries_notes import _create_author


def _create(db_session, sha256_hash="a" * 64):
    import_run = create_import_run(db_session)
    return create_import_document(
        db_session,
        import_run.import_run_id,
        f"import_documents/asr/{uuid.uuid4()}",
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
        db_session, import_run.import_run_id, f"import_documents/asr/{uuid.uuid4()}", "a.xlsx", "text/csv", "a" * 64
    )
    create_import_document(
        db_session, import_run.import_run_id, f"import_documents/asr/{uuid.uuid4()}", "b.xlsx", "text/csv", "b" * 64
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


def test_get_import_document_by_hash(db_session):
    _create(db_session, sha256_hash="a" * 64)

    assert get_import_documents_by_hash(db_session, "a" * 64) is not None
    assert get_import_documents_by_hash(db_session, "b" * 64) is None


def test_get_import_documents_by_run_is_scoped(db_session):
    # _create makes its own author, and a second call collides on employee_id.
    _create_author(db_session)
    run_a = make_import_run(
        db_session, SourceType.ASR, "9999999", "a.xlsx", ImportStatus.PENDING, 10
    )
    run_b = make_import_run(
        db_session, SourceType.UCT_MARKS, "9999999", "b.xlsx", ImportStatus.PENDING, 5
    )
    create_import_document(
        db_session, run_a.import_run_id, "key-a", "a.xlsx", "application/vnd.ms-excel", "a" * 64
    )
    create_import_document(
        db_session, run_b.import_run_id, "key-b", "b.xlsx", "application/vnd.ms-excel", "b" * 64
    )

    found = get_import_documents_by_run(db_session, run_a.import_run_id)
    assert [d.original_file_name for d in found] == ["a.xlsx"]


def test_get_import_documents_by_run_empty(db_session):
    import_run = create_import_run(db_session)

    assert get_import_documents_by_run(db_session, import_run.import_run_id) == []
