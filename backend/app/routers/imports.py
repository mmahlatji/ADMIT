"""Endpoints for uploading source spreadsheets and reconciling them into the DB."""

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.import_runs import ImportRun, SourceType
from app.models.users import RoleEnum, User
from app.schemas.import_runs import ImportRunResponse
from app.services.imports.orchestrator import run_import

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/{source_type}", response_model=ImportRunResponse, status_code=status.HTTP_201_CREATED)
def upload_import(
    source_type: SourceType,
    file: UploadFile,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
) -> ImportRun:
    """Upload one source spreadsheet and reconcile it into the database.

    CSV only for now - reading .xlsx would need openpyxl, which isn't a
    dependency yet.
    """
    if actor.employee_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Your profile has no employee_id set yet, so this import can't be attributed to you",
        )
    sheet = pd.read_csv(file.file)
    return run_import(
        db, source_type=source_type, uploaded_by=actor.employee_id, file_name=file.filename, sheet=sheet
    )
