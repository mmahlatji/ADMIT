"""End-to-end bucket check: upload a real ASR sheet through the HTTP router,
write DB rows to the in-memory SQLite fixture, and push the file to the real
Supabase `import_documents` bucket.

Skipped (not failed) when Supabase env vars aren't set, so CI / offline runs
are unaffected. Requires the October ASR sheet in the repo root and openpyxl.
"""

import uuid
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import get_settings
from app.deps import get_current_user, get_db
from app.main import app
from app.models.academic_plans import AcademicPlanType
from app.models.import_documents import Document
from app.models.import_runs import ImportStatus
from app.models.users import RoleEnum
from app.queries.academic_plans import create_academic_plan
from app.queries.departments import create_department
from app.queries.storage import bucket as storage_queries
from app.services.storage import import_documents as storage_service
from tests.support import request_scoped_db
from tests.test_queries_notes import _create_author

pytestmark = pytest.mark.skipif(
    not get_settings().supabase_url or not get_settings().supabase_secret_key,
    reason="Supabase storage not configured",
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASR_SHEET = _REPO_ROOT / "CSC - ASR - 2023 - October 2022.xlsx"


def _seed(db_session):
    actor = _create_author(db_session, employee_id="9999999")
    actor.role = RoleEnum.convenor
    create_department(db_session, "CSC", "Computer Science")
    create_academic_plan(db_session, "CSC", "SH001CSC05", AcademicPlanType.INTERNAL)
    create_academic_plan(db_session, "CSC", "SH001CSC06", AcademicPlanType.EXTERNAL)
    return actor


def _make_client(db_session, actor):
    app.dependency_overrides[get_db] = request_scoped_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: actor
    return TestClient(app)


def _teardown():
    app.dependency_overrides.clear()


def test_upload_via_router_stores_in_sqlite_and_bucket(db_session):
    pytest.importorskip("openpyxl")
    if not _ASR_SHEET.exists():
        pytest.skip("real ASR sheet not present in the repo root")

    actor = _seed(db_session)
    client = _make_client(db_session, actor)

    content = _ASR_SHEET.read_bytes()
    document = None
    try:
        res = client.post(
            "/imports/asr",
            files={
                "file": (
                    _ASR_SHEET.name,
                    content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["status"] == ImportStatus.COMPLETED.value

        import_run_id = uuid.UUID(body["import_run_id"])
        document = db_session.execute(
            select(Document).where(Document.import_run_id == import_run_id)
        ).scalar_one()

        signed_url = storage_service.get_signed_url(document.storage_key)
        assert signed_url is not None
        resp = httpx.get(signed_url)
        assert resp.status_code == 200
        assert resp.content == content
        print(f"UPLOAD OK -> storage_key={document.storage_key}\nSIGNED_URL={signed_url}")
    finally:
        if document is not None:
            storage_queries.delete_file("import_documents", document.storage_key)
        _teardown()
