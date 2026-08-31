import uuid

from fastapi.testclient import TestClient

from app.deps import get_current_user, get_db
from app.main import app
from app.models.users import RoleEnum, User
from app.routers import import_documents as import_documents_router
from app.services import import_documents as document_service
from tests.test_queries_import_runs import _create as create_import_run


def _make_actor(role=RoleEnum.convenor):
    # a role is required now: this endpoint hands back a signed URL to the raw
    # sheet, so an unapproved signup (role None) must not reach it
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
    import_run = create_import_run(db_session)
    return document_service.create_document(
        db_session,
        import_run.import_run_id,
        "import_documents/asr/abc.xlsx",
        "asr.xlsx",
        "application/vnd.ms-excel",
        "a" * 64,
    )


def test_download_document_returns_signed_url(db_session, monkeypatch):
    document = _create_document(db_session)
    actor = _make_actor()
    monkeypatch.setattr(
        import_documents_router.import_doc_storage_service,
        "get_signed_url",
        lambda key: f"https://example.com/{key}",
    )

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/import_documents/{document.document_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["original_file_name"] == "asr.xlsx"
        assert body["content_type"] == "application/vnd.ms-excel"
        assert body["signed_url"] == f"https://example.com/{document.storage_key}"
    finally:
        _teardown()


def test_download_document_not_found(db_session):
    actor = _make_actor()

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/import_documents/{uuid.uuid4()}")
        assert res.status_code == 404
    finally:
        _teardown()


def test_download_document_missing_signed_url(db_session, monkeypatch):
    document = _create_document(db_session)
    actor = _make_actor()
    monkeypatch.setattr(
        import_documents_router.import_doc_storage_service, "get_signed_url", lambda key: None
    )

    client = _make_client(db_session, actor)
    try:
        res = client.get(f"/import_documents/{document.document_id}")
        assert res.status_code == 500
    finally:
        _teardown()


def test_download_document_rejects_user_without_a_role(db_session):
    # signed up but not yet approved: must not be able to pull the raw sheet
    document = _create_document(db_session)
    client = _make_client(db_session, _make_actor(role=None))
    try:
        response = client.get(f"/import_documents/{document.document_id}")
        assert response.status_code == 403
    finally:
        _teardown()
