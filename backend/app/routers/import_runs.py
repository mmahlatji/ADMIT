import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.import_documents import DocumentResponse
from app.schemas.import_runs import ImportRunResponse
from app.services import import_documents as document_service
from app.services import import_runs as import_runs_service

router = APIRouter(prefix="/import_runs", tags=["import_runs"])

MAX_PAGE_SIZE = 500


@router.get("", response_model=list[ImportRunResponse])
def list_import_runs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    return import_runs_service.list_import_runs(db, skip=skip, limit=limit)


@router.get("/{import_run_id}", response_model=ImportRunResponse)
def get_import_run(
    import_run_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    import_run = import_runs_service.get_import_run_by_id(db, import_run_id)
    if import_run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Import run not found")
    return import_run


@router.get("/{import_run_id}/documents", response_model=list[DocumentResponse])
def list_run_documents(
    import_run_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    """List the files this run was created from.

    The counterpart to the applicant documents listing: an import run carried
    no reference to its own source file, so GET /import_documents/{id} was
    likewise uncallable from anywhere.
    """
    import_run = import_runs_service.get_import_run_by_id(db, import_run_id)
    if import_run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Import run not found")
    return document_service.list_documents_for_run(db, import_run_id)
