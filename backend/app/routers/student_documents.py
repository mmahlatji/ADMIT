import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.student_documents import StudentDocumentDownloadResponse
from app.services import student_documents as document_service
from app.services.storage import student_documents as student_doc_storage_service

router = APIRouter(prefix="/student_documents", tags=["student_documents"])

ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.committee, RoleEnum.admin]


@router.get(
    "/{document_id}",
    response_model=StudentDocumentDownloadResponse,
    status_code=status.HTTP_200_OK,
)
def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role(*ALLOWED_ROLES)),
):
    document = document_service.get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document does not exist")
    signed_url = student_doc_storage_service.get_signed_url(document.storage_key)

    if signed_url is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Download link not created")
    return {
        "original_file_name": document.original_file_name,
        "signed_url": signed_url,
        "content_type": document.content_type,
    }
