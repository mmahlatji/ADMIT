import hashlib
import uuid
from types import SimpleNamespace

import pytest

from app.models.import_runs import ImportStatus, SourceType
from app.services.storage import import_documents as svc
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
    FileUploadFailedException,
)


class FakeFile:
    def __init__(self, filename, content_type, content):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self):
        return self._content


def _import_run():
    return SimpleNamespace(import_run_id=uuid.uuid4(), source_type=SourceType.ASR)


@pytest.mark.asyncio
async def test_empty_file_raises():
    with pytest.raises(FileEmptyException):
        await svc.upload_document(
            None, _import_run(), FakeFile("asr.xlsx", "application/vnd.ms-excel", b"")
        )


@pytest.mark.asyncio
async def test_too_large_file_raises():
    content = b"x" * (svc.MAX_FILE_SIZE + 1)
    with pytest.raises(FileTooLargeException):
        await svc.upload_document(
            None, _import_run(), FakeFile("asr.xlsx", "application/vnd.ms-excel", content)
        )


@pytest.mark.asyncio
async def test_disallowed_extension_raises():
    with pytest.raises(FileNotAllowedException):
        await svc.upload_document(
            None, _import_run(), FakeFile("asr.txt", "text/plain", b"hello")
        )


@pytest.mark.asyncio
async def test_duplicate_hash_raises_when_prior_run_succeeded(monkeypatch):
    existing = SimpleNamespace(import_run_id=uuid.uuid4())
    monkeypatch.setattr(svc.import_doc_queries, "get_document_by_hash", lambda db, h: existing)
    monkeypatch.setattr(
        svc.import_run_queries, "get_import_run_by_id",
        lambda db, rid: SimpleNamespace(status=ImportStatus.COMPLETED),
    )

    with pytest.raises(FileAlreadyExistsException):
        await svc.upload_document(
            None, _import_run(), FakeFile("asr.csv", "text/csv", b"hello")
        )


@pytest.mark.asyncio
async def test_duplicate_hash_allows_retry_after_a_failed_run(monkeypatch):
    # a failed import has to be retryable with the same file: blocking on the
    # hash alone left no way to re-run it once the cause was fixed
    existing = SimpleNamespace(import_run_id=uuid.uuid4())
    run = _import_run()
    monkeypatch.setattr(svc.import_doc_queries, "get_document_by_hash", lambda db, h: existing)
    monkeypatch.setattr(
        svc.import_run_queries, "get_import_run_by_id",
        lambda db, rid: SimpleNamespace(status=ImportStatus.FAILED),
    )
    repointed = {}

    def fake_update(db, document, **kwargs):
        repointed.update(kwargs)
        return document

    monkeypatch.setattr(svc, "import_doc_queries_update", fake_update)

    result = await svc.upload_document(
        None, run, FakeFile("asr.csv", "text/csv", b"hello")
    )
    assert result is existing
    # reuses the object already in storage, just points it at the new run
    assert repointed == {"import_run_id": run.import_run_id}


@pytest.mark.asyncio
async def test_upload_failure_raises(monkeypatch):
    monkeypatch.setattr(svc.import_doc_queries, "get_document_by_hash", lambda db, h: None)

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(svc.import_queries, "upload_documents", boom)

    with pytest.raises(FileUploadFailedException):
        await svc.upload_document(
            None, _import_run(), FakeFile("asr.csv", "text/csv", b"hello")
        )


@pytest.mark.asyncio
async def test_db_failure_deletes_orphaned_storage(monkeypatch):
    storage_key = "import_documents/asr/abc"
    monkeypatch.setattr(svc.import_doc_queries, "get_document_by_hash", lambda db, h: None)
    monkeypatch.setattr(svc.import_queries, "upload_documents", lambda *a, **k: storage_key)

    deleted = []
    monkeypatch.setattr(svc.import_queries, "delete_document", lambda key: deleted.append(key))

    def boom(*args, **kwargs):
        raise RuntimeError("db failed")

    monkeypatch.setattr(svc.import_doc_queries, "create_document", boom)

    with pytest.raises(RuntimeError):
        await svc.upload_document(
            None, _import_run(), FakeFile("asr.csv", "text/csv", b"hello")
        )

    assert deleted == [storage_key]


@pytest.mark.asyncio
async def test_success_returns_document(monkeypatch):
    storage_key = "import_documents/asr/abc"
    result = object()
    calls = {}

    monkeypatch.setattr(svc.import_doc_queries, "get_document_by_hash", lambda db, h: None)

    def upload(content, content_type, extension, import_type):
        calls["upload"] = (content, content_type, extension, import_type)
        return storage_key

    def create(db, import_run_id, storage_key, sha256_hash, original_file_name, content_type):
        calls["create"] = (import_run_id, storage_key, sha256_hash, original_file_name, content_type)
        return result

    monkeypatch.setattr(svc.import_queries, "upload_documents", upload)
    monkeypatch.setattr(svc.import_doc_queries, "create_document", create)

    import_run = _import_run()
    document = await svc.upload_document(
        None, import_run, FakeFile("asr.csv", "text/csv", b"hello")
    )

    assert document is result
    assert calls["upload"] == (b"hello", "text/csv", ".csv", SourceType.ASR)
    assert calls["create"] == (
        import_run.import_run_id,
        storage_key,
        hashlib.sha256(b"hello").hexdigest(),
        "asr.csv",
        "text/csv",
    )


def test_get_signed_url(monkeypatch):
    monkeypatch.setattr(
        svc.import_queries, "generate_signed_url", lambda key: f"https://example.com/{key}"
    )

    assert svc.get_signed_url("import_documents/asr/abc") == "https://example.com/import_documents/asr/abc"
