import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.deps import get_current_user, get_db
from app.main import app
from app.models.users import RoleEnum, User
from app.routers import applicants as applicants_router
from app.routers import student_documents as student_documents_router
from app.services import student_documents as document_service
from tests.test_queries_applicants import _create as create_applicant


def _make_actor(role=RoleEnum.convenor):
    return User(
        user_id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@uct.ac.za",
        employee_id="1111111",
        role=role,
    )


def _make_client(db_session, actor):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: actor
    return TestClient(app)


def _teardown():
    app.dependency_overrides.clear()


def _create_document(db_session):
    applicant = create_applicant(db_session)
    return document_service.create_document(
        db_session,
        applicant.applicant_id,
        "student_documents/abc/t.pdf",
        "t.pdf",
        "application/pdf",
        "a" * 64,
    )


def _fake_document(applicant_id):
    return SimpleNamespace(
        document_id=uuid.uuid4(),
        applicant_id=applicant_id,
        storage_key="student_documents/abc/t.pdf",
        original_file_name="t.pdf",
        content_type="application/pdf",
        sha256_hash="a" * 64,
        uploaded_at=datetime.now(UTC),
    )


def test_download_document_returns_signed_url(db_session, monkeypatch):
    document = _create_document(db_session)
    actor = _make_actor()
    monkeypatch.setattr(
        student_documents_router.student_doc_storage_service,
        "get_signed_url",
        lambda key: f"https://example.com/{key}",
    )

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/student_documents/{document.document_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["original_file_name"] == "t.pdf"
        assert body["content_type"] == "application/pdf"
        assert body["signed_url"] == f"https://example.com/{document.storage_key}"
    finally:
        _teardown()


def test_download_document_not_found(db_session):
    client = _make_client(db_session, _make_actor())
    try:
        res = client.get(f"/student_documents/{uuid.uuid4()}")
        assert res.status_code == 404
    finally:
        _teardown()


def test_download_document_missing_signed_url(db_session, monkeypatch):
    document = _create_document(db_session)
    monkeypatch.setattr(
        student_documents_router.student_doc_storage_service, "get_signed_url", lambda key: None
    )

    client = _make_client(db_session, _make_actor())
    try:
        res = client.get(f"/student_documents/{document.document_id}")
        assert res.status_code == 500
    finally:
        _teardown()


def test_download_document_rejects_user_without_a_role(db_session):
    document = _create_document(db_session)
    client = _make_client(db_session, _make_actor(role=None))
    try:
        res = client.get(f"/student_documents/{document.document_id}")
        assert res.status_code == 403
    finally:
        _teardown()


def test_upload_document_returns_created(db_session, monkeypatch):
    applicant = create_applicant(db_session)
    doc = _fake_document(applicant.applicant_id)

    async def fake_upload(db, applicant_id, campus_id, content, extension, original_file_name):
        return doc

    monkeypatch.setattr(applicants_router.student_doc_storage, "upload_document", fake_upload)

    client = _make_client(db_session, _make_actor())
    try:
        res = client.post(
            f"/applicants/{applicant.campus_id}/documents",
            files={"file": ("t.pdf", b"%PDF-1.4\n...", "application/pdf")},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["document_id"] == str(doc.document_id)
        assert body["original_file_name"] == "t.pdf"
        assert body["applicant_id"] == str(applicant.applicant_id)
    finally:
        _teardown()


def test_upload_document_applicant_not_found(db_session):
    client = _make_client(db_session, _make_actor())
    try:
        res = client.post(
            "/applicants/nope/documents",
            files={"file": ("t.pdf", b"%PDF-1.4\n...", "application/pdf")},
        )
        assert res.status_code == 404
    finally:
        _teardown()


def test_upload_document_rejects_disallowed_type(db_session):
    # the .pdf filename lies: content is HTML, detected as text/csv, rejected
    applicant = create_applicant(db_session)

    client = _make_client(db_session, _make_actor())
    try:
        res = client.post(
            f"/applicants/{applicant.campus_id}/documents",
            files={"file": ("t.pdf", b"<html>not a pdf</html>", "application/pdf")},
        )
        assert res.status_code == 415
    finally:
        _teardown()
