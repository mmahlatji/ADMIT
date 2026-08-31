import uuid

from app.services import import_documents as service
from tests.test_queries_import_runs import _create as create_import_run


def test_get_document_by_hash(db_session):
    import_run = create_import_run(db_session)
    document = service.create_document(
        db_session,
        import_run.import_run_id,
        "import_documents/asr/abc",
        "asr.xlsx",
        "application/vnd.ms-excel",
        "a" * 64,
    )

    fetched = service.get_document_by_hash(db_session, "a" * 64)
    assert fetched.document_id == document.document_id
    assert service.get_document_by_hash(db_session, "b" * 64) is None


def test_get_document_by_id(db_session):
    import_run = create_import_run(db_session)
    document = service.create_document(
        db_session,
        import_run.import_run_id,
        "import_documents/asr/abc",
        "asr.xlsx",
        "application/vnd.ms-excel",
        "a" * 64,
    )

    fetched = service.get_document_by_id(db_session, document.document_id)
    assert fetched.document_id == document.document_id
    assert service.get_document_by_id(db_session, uuid.uuid4()) is None


def test_create_document(db_session):
    import_run = create_import_run(db_session)

    document = service.create_document(
        db_session,
        import_run.import_run_id,
        "import_documents/asr/xyz",
        "asr.csv",
        "text/csv",
        "c" * 64,
    )

    assert document.original_file_name == "asr.csv"
    assert document.storage_key == "import_documents/asr/xyz"
    assert document.sha256_hash == "c" * 64
