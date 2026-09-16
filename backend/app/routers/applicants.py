from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.applicants import ApplicantDetail, ApplicantResponse
from app.schemas.student_documents import StudentDocumentResponse
from app.services import applicants as applicants_service
from app.services.storage import student_documents as student_doc_storage
from app.services.storage.base import read_and_validate
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
    FileUploadFailedException,
)

router = APIRouter(prefix="/applicants", tags=["applicants"])

ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get("", response_model=list[ApplicantResponse])
def list_applicants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    return applicants_service.list_applicants(db, skip=skip, limit=limit)


@router.get("/{campus_id}", response_model=ApplicantDetail)
def get_applicant(
    campus_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*ALLOWED_ROLES)),
):
    applicant = applicants_service.get_applicant_by_campus_id(db, campus_id)
    if applicant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Applicant not found")
    return applicant


@router.post(
    "/{campus_id}/documents",
    response_model=StudentDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    campus_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(RoleEnum.convenor, RoleEnum.admin)),
):
    """Upload one document for an applicant."""
    applicant = applicants_service.get_applicant_by_campus_id(db, campus_id)
    if applicant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Applicant not found")

    try:
        content, extension = await read_and_validate(
            file, student_doc_storage.STUDENT_DOCUMENT_EXTENSIONS
        )
        return await student_doc_storage.upload_document(
            db,
            applicant.applicant_id,
            applicant.campus_id,
            content,
            extension,
            file.filename,
        )
    except FileEmptyException as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except FileNotAllowedException as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except FileTooLargeException as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(exc)) from exc
    except FileAlreadyExistsException as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except FileUploadFailedException as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc
