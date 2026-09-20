import uuid

from fastapi.testclient import TestClient

from app.deps import get_current_user, get_db
from app.main import app
from app.models.users import RoleEnum, User
from app.routers import imports as imports_router
from tests.support import request_scoped_db


def _make_actor(role=RoleEnum.convenor):
    return User(
        user_id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@uct.ac.za",
        employee_id="1111111",
        role=role,
    )


def _make_client(db_session, actor):
    app.dependency_overrides[get_db] = request_scoped_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: actor
    return TestClient(app)


def _teardown():
    app.dependency_overrides.clear()


def _multipart_body_with_empty_filename(content: bytes, content_type: str) -> tuple[bytes, str]:
    """Build a multipart body with Content-Disposition: filename="".

    httpx's files= helper only ever sends a real filename or omits the
    attribute (see _multipart.py: `if self.filename:`), so it cannot itself
    produce this on the wire. A part with an empty filename is still
    something a non-browser client can send, and it's what actually makes
    Starlette build an UploadFile with filename == "".
    """
    boundary = "testboundary123"
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename=""\r\n'
        f'Content-Type: {content_type}\r\n\r\n'
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def test_upload_import_falls_back_when_filename_is_missing(db_session, monkeypatch):
    """A non-browser client can send an empty filename attribute, which
    Starlette turns into UploadFile(filename=""). NOT NULL does not reject
    an empty string, so without a fallback the run silently stores a
    useless file_name instead of a real one.
    """

    async def fake_upload_document(**kwargs):
        return None

    def fake_run_import(db, import_run, sheet):
        return import_run

    monkeypatch.setattr(
        imports_router.import_doc_service, "upload_document", fake_upload_document
    )
    monkeypatch.setattr(imports_router, "run_import", fake_run_import)

    body, content_type = _multipart_body_with_empty_filename(
        b"col1,col2\n1,2\n", "text/csv"
    )

    client = _make_client(db_session, _make_actor())
    try:
        res = client.post(
            "/imports/asr",
            content=body,
            headers={"Content-Type": content_type},
        )
        assert res.status_code == 201
        assert res.json()["file_name"] == "import.csv"
    finally:
        _teardown()


def test_upload_import_keeps_the_real_filename(db_session, monkeypatch):
    async def fake_upload_document(**kwargs):
        return None

    def fake_run_import(db, import_run, sheet):
        return import_run

    monkeypatch.setattr(
        imports_router.import_doc_service, "upload_document", fake_upload_document
    )
    monkeypatch.setattr(imports_router, "run_import", fake_run_import)

    client = _make_client(db_session, _make_actor())
    try:
        res = client.post(
            "/imports/asr",
            files={"file": ("applicants.csv", b"col1,col2\n1,2\n", "text/csv")},
        )
        assert res.status_code == 201
        assert res.json()["file_name"] == "applicants.csv"
    finally:
        _teardown()

def test_upload_import_rejects_a_file_pandas_cannot_parse(db_session, monkeypatch):
    """A sheet that will not parse is a bad file, not a server fault: it used
    to escape as an unhandled ParserError and 500."""

    async def fake_upload_document(**kwargs):
        return None

    monkeypatch.setattr(
        imports_router.import_doc_service, "upload_document", fake_upload_document
    )

    # ragged columns: the C parser cannot tokenise this
    broken = b"""a,b,c
1,2
3,4,5,6,7
"""

    client = _make_client(db_session, _make_actor())
    try:
        res = client.post(
            "/imports/asr",
            files={"file": ("broken.csv", broken, "text/csv")},
        )
        assert res.status_code == 400
        assert "could not be read as a spreadsheet" in res.json()["detail"]
    finally:
        _teardown()
