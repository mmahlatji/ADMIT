import hashlib
import uuid
from types import SimpleNamespace

import pytest

from app.models.import_runs import ImportStatus, SourceType
from app.services.storage import base
from app.services.storage import import_documents as svc
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileUploadFailedException,
)


def _import_run():
    return SimpleNamespace(import_run_id=uuid.uuid4(), source_type=SourceType.ASR)


@pytest.mark.asyncio
async def test_duplicate_hash_raises_when_prior_run_succeeded(monkeypatch):
    existing = SimpleNamespace(import_run_id=uuid.uuid4())
    monkeypatch.setattr(svc.import_doc_service, "get_document_by_hash", lambda db, h: existing)
    monkeypatch.setattr(
        svc.import_run_service, "get_import_run_by_id",
        lambda db, rid: SimpleNamespace(status=ImportStatus.COMPLETED),
    )

    with pytest.raises(FileAlreadyExistsException):
        await svc.upload_document(None, _import_run(), b"hello", ".csv", "asr.csv")


@pytest.mark.asyncio
async def test_duplicate_hash_allows_retry_after_a_failed_run(monkeypatch):
    # a failed import has to be retryable with the same file: blocking on the
    # hash alone left no way to re-run it once the cause was fixed
    existing = SimpleNamespace(import_run_id=uuid.uuid4())
    run = _import_run()
    monkeypatch.setattr(svc.import_doc_service, "get_document_by_hash", lambda db, h: existing)
    monkeypatch.setattr(
        svc.import_run_service, "get_import_run_by_id",
        lambda db, rid: SimpleNamespace(status=ImportStatus.FAILED),
    )
    repointed = {}

    def fake_update(db, document, **kwargs):
        repointed.update(kwargs)
        return document

    monkeypatch.setattr(svc, "update_import_document", fake_update)

    result = await svc.upload_document(None, run, b"hello", ".csv", "asr.csv")
    assert result is existing
    # reuses the object already in storage, just points it at the new run
    assert repointed == {"import_run_id": run.import_run_id}


@pytest.mark.asyncio
async def test_upload_failure_raises(monkeypatch):
    monkeypatch.setattr(svc.import_doc_service, "get_document_by_hash", lambda db, h: None)

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(base.storage, "upload_file", boom)

    with pytest.raises(FileUploadFailedException):
        await svc.upload_document(None, _import_run(), b"hello", ".csv", "asr.csv")


@pytest.mark.asyncio
async def test_db_failure_deletes_orphaned_storage(monkeypatch):
    monkeypatch.setattr(svc.import_doc_service, "get_document_by_hash", lambda db, h: None)
    uploaded = {}

    def fake_upload(bucket, content, content_type, storage_path):
        uploaded["path"] = storage_path
        return storage_path

    monkeypatch.setattr(base.storage, "upload_file", fake_upload)

    deleted = []
    monkeypatch.setattr(base.storage, "delete_file", lambda bucket, key: deleted.append(key))

    def boom(*args, **kwargs):
        raise RuntimeError("db failed")

    monkeypatch.setattr(svc.import_doc_service, "create_document", boom)

    with pytest.raises(RuntimeError):
        await svc.upload_document(None, _import_run(), b"hello", ".csv", "asr.csv")

    assert deleted == [uploaded["path"]]


@pytest.mark.asyncio
async def test_success_returns_document(monkeypatch):
    result = object()
    calls = {}

    monkeypatch.setattr(svc.import_doc_service, "get_document_by_hash", lambda db, h: None)

    def upload(bucket, content, content_type, storage_path):
        calls["upload"] = (bucket, content, content_type, storage_path)
        return storage_path

    def create(db, import_run_id, storage_key, original_file_name, content_type, sha256_hash):
        calls["create"] = (import_run_id, storage_key, sha256_hash, original_file_name, content_type)
        return result

    monkeypatch.setattr(base.storage, "upload_file", upload)
    monkeypatch.setattr(svc.import_doc_service, "create_document", create)

    import_run = _import_run()
    document = await svc.upload_document(None, import_run, b"hello", ".csv", "asr.csv")

    assert document is result
    bucket, content, content_type, storage_path = calls["upload"]
    assert bucket == "import_documents"
    assert content == b"hello"
    assert content_type == "text/csv"
    assert storage_path.startswith("asr/")
    assert storage_path.endswith(".csv")
    assert calls["create"] == (
        import_run.import_run_id,
        storage_path,
        hashlib.sha256(b"hello").hexdigest(),
        "asr.csv",
        "text/csv",
    )


def test_get_signed_url(monkeypatch):
    monkeypatch.setattr(
        base.storage,
        "generate_signed_url",
        lambda bucket, key, expires: f"https://example.com/{key}",
    )

    assert svc.get_signed_url("import_documents/asr/abc") == "https://example.com/import_documents/asr/abc"
