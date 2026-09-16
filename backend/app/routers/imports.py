"""Endpoints for uploading source spreadsheets and reconciling them into the DB."""

import io

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
from app.services.storage.base import read_and_validate
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


@router.post(
    "/{source_type}",
    response_model=ImportRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_import(
    source_type: SourceType,
    file: UploadFile,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
) -> ImportRun:
    """Upload one source spreadsheet and reconcile it into the database.

    Accepts .csv and .xlsx by content, see TO_DATAFRAME above.
    """

    try:
        content, extension = await read_and_validate(
            file, import_doc_service.IMPORT_DOCUMENT_EXTENSIONS
        )
    except FileEmptyException as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except FileNotAllowedException as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except FileTooLargeException as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(exc)) from exc

    sheet = await run_in_threadpool(TO_DATAFRAME[extension], io.BytesIO(content))

    import_run = import_run_service.create_import_run(
        db,
        source_type=source_type,
        uploaded_by=actor.employee_id,
        # Starlette only builds an UploadFile when Content-Disposition
        # carries a filename, but that attribute can be empty ("") for a
        # non-browser client. NOT NULL does not reject an empty string, so
        # without this the run would store a genuinely useless file_name
        # rather than fail loudly.
        file_name=file.filename or f"import{extension}",
        status=ImportStatus.PROCESSING,
        rows_total=len(sheet),
    )

    try:
        await import_doc_service.upload_document(
            db=db,
            import_run=import_run,
            content=content,
            extension=extension,
            original_file_name=file.filename,
        )
    except FileAlreadyExistsException as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except FileUploadFailedException as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc

    # run_import is sync and does the whole sheet inline (~16 queries a row), so
    # calling it directly from this async endpoint would block the event loop and
    # hang every other request for the duration. Hand it to a worker thread,
    # which is what FastAPI does for sync endpoints anyway. The upload above is
    # genuinely async, so the endpoint itself has to stay async.
    return await run_in_threadpool(run_import, db, import_run, sheet=sheet)
