import hashlib
import uuid
from types import SimpleNamespace

import pytest

from app.services.storage import base
from app.services.storage import student_documents as svc
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileUploadFailedException,
)


@pytest.mark.asyncio
async def test_duplicate_hash_raises(monkeypatch):
    monkeypatch.setattr(
        svc.student_doc_service, "get_document_by_hash", lambda db, a, h: SimpleNamespace()
    )

    with pytest.raises(FileAlreadyExistsException):
        await svc.upload_document(
            None, uuid.uuid4(), "xxxyyy001", b"%PDF-1.4\n", ".pdf", "t.pdf"
        )


@pytest.mark.asyncio
async def test_upload_failure_raises(monkeypatch):
    monkeypatch.setattr(svc.student_doc_service, "get_document_by_hash", lambda db, a, h: None)

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(base.storage, "upload_file", boom)

    with pytest.raises(FileUploadFailedException):
        await svc.upload_document(
            None, uuid.uuid4(), "xxxyyy001", b"%PDF-1.4\n", ".pdf", "t.pdf"
        )


@pytest.mark.asyncio
async def test_db_failure_deletes_orphaned_storage(monkeypatch):
    monkeypatch.setattr(svc.student_doc_service, "get_document_by_hash", lambda db, a, h: None)
    uploaded = {}

    def fake_upload(bucket, content, content_type, storage_path):
        uploaded["path"] = storage_path
        return storage_path

    monkeypatch.setattr(base.storage, "upload_file", fake_upload)

    deleted = []
    monkeypatch.setattr(base.storage, "delete_file", lambda bucket, key: deleted.append(key))

    def boom(*args, **kwargs):
        raise RuntimeError("db failed")

    monkeypatch.setattr(svc.student_doc_service, "create_document", boom)

    with pytest.raises(RuntimeError):
        await svc.upload_document(
            None, uuid.uuid4(), "xxxyyy001", b"%PDF-1.4\n", ".pdf", "t.pdf"
        )

    assert deleted == [uploaded["path"]]


@pytest.mark.asyncio
async def test_success_returns_document(monkeypatch):
    result = object()
    calls = {}
    applicant_id = uuid.uuid4()
    campus_id = "xxxyyy001"
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

    monkeypatch.setattr(svc.student_doc_service, "get_document_by_hash", lambda db, a, h: None)

    def upload(bucket, content, content_type, storage_path):
        calls["upload"] = (bucket, content, content_type, storage_path)
        return storage_path

    def create(db, applicant_id, storage_key, original_file_name, content_type, sha256_hash):
        calls["create"] = (applicant_id, storage_key, original_file_name, content_type, sha256_hash)
        return result

    monkeypatch.setattr(base.storage, "upload_file", upload)
    monkeypatch.setattr(svc.student_doc_service, "create_document", create)

    document = await svc.upload_document(
        None, applicant_id, campus_id, content, ".pdf", "t.pdf"
    )

    assert document is result
    bucket, uploaded_content, content_type, storage_path = calls["upload"]
    assert bucket == "student_documents"
    assert uploaded_content == content
    assert content_type == "application/pdf"
    assert storage_path.startswith(f"{campus_id}/")
    assert storage_path.endswith(".pdf")
    assert calls["create"] == (
        applicant_id,
        storage_path,
        "t.pdf",
        "application/pdf",
        hashlib.sha256(content).hexdigest(),
    )


def test_get_signed_url(monkeypatch):
    monkeypatch.setattr(
        base.storage,
        "generate_signed_url",
        lambda bucket, key, expires: f"https://example.com/{key}",
    )

    assert svc.get_signed_url("student_documents/abc/t.pdf") == "https://example.com/student_documents/abc/t.pdf"


@pytest.mark.asyncio
async def test_same_file_from_a_second_applicant_is_stored(db_session, monkeypatch):
    """The hash is unique per applicant, not globally.

    Two applicants can legitimately send byte-identical files, e.g. the same
    blank form. Rejecting the second one refused a real document and told its
    uploader that somebody else had already sent that exact file.
    """
    from app.queries.student_documents import create_student_document
    from tests.test_queries_applicants import _create as create_applicant

    content = b"%PDF-1.4\nblank consent form\n"
    digest = hashlib.sha256(content).hexdigest()

    first = create_applicant(db_session, campus_id="aaabbb001")
    create_student_document(
        db_session, first.applicant_id, "aaabbb001/x.pdf", "form.pdf", "application/pdf", digest
    )
    second = create_applicant(db_session, campus_id="cccddd002", employee_id="1000002")

    monkeypatch.setattr(base.storage, "upload_file", lambda b, c, t, p: p)

    document = await svc.upload_document(
        db_session, second.applicant_id, second.campus_id, content, ".pdf", "form.pdf"
    )

    assert document.applicant_id == second.applicant_id
    assert document.sha256_hash == digest


@pytest.mark.asyncio
async def test_same_applicant_resending_the_same_file_is_rejected(db_session):
    content = b"%PDF-1.4\ntranscript\n"
    digest = hashlib.sha256(content).hexdigest()

    from app.queries.student_documents import create_student_document
    from tests.test_queries_applicants import _create as create_applicant

    applicant = create_applicant(db_session, campus_id="aaabbb001")
    create_student_document(
        db_session, applicant.applicant_id, "aaabbb001/x.pdf", "t.pdf", "application/pdf", digest
    )

    with pytest.raises(FileAlreadyExistsException):
        await svc.upload_document(
            db_session, applicant.applicant_id, applicant.campus_id, content, ".pdf", "t.pdf"
        )
