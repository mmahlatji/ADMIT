"""Endpoints for uploading source spreadsheets and reconciling them into the DB."""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.import_runs import ImportRun, ImportStatus, SourceType
from app.models.users import RoleEnum, User
from app.schemas.import_runs import ImportRunResponse
from app.services import import_runs as import_run_service
from app.services.imports.orchestrator import run_import
from app.services.storage import import_documents as import_doc_service
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
    FileUploadFailedException,
)

router = APIRouter(prefix="/imports", tags=["imports"])


TO_DATAFRAME = {
    ".xlsx": pd.read_excel,
    ".csv": pd.read_csv,
}


@router.post("/{source_type}", response_model=ImportRunResponse, status_code=status.HTTP_201_CREATED)
async def upload_import(
    source_type: SourceType,
    file: UploadFile,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
) -> ImportRun:
    """Upload one source spreadsheet and reconcile it into the database.

    Accepts .csv and .xlsx, see TO_DATAFRAME above.
    """
    if actor.employee_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Your profile has no employee_id set yet, so this import can't be attributed to you",
        )
    
    extension = Path(file.filename).suffix.lower()
    pd_func = TO_DATAFRAME.get(extension)
    if pd_func is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    sheet = pd_func(file.file)

    # upload the file
    import_run = import_run_service.create_import_run(
            db,
            source_type=source_type,
            uploaded_by=actor.employee_id,
            file_name=file.filename,
            status=ImportStatus.PROCESSING,
            rows_total=len(sheet),
        )

    # pd_func(file.file) above left the stream at EOF, so rewind it or the
    # upload below would read 0 bytes and raise FileEmptyException.
    await file.seek(0)

    try:
        await import_doc_service.upload_document(
            db=db,
            import_run=import_run,
            file=file
        )
    except FileEmptyException as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except FileNotAllowedException as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc))
    except FileTooLargeException as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(exc))
    except FileAlreadyExistsException as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    except FileUploadFailedException as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
    
    # run_import is sync and does the whole sheet inline (~16 queries a row), so
    # calling it directly from this async endpoint would block the event loop and
    # hang every other request for the duration. Hand it to a worker thread,
    # which is what FastAPI does for sync endpoints anyway. The upload above is
    # genuinely async, so the endpoint itself has to stay async.
    return await run_in_threadpool(run_import, db, import_run, sheet=sheet)


