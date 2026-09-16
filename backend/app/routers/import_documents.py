import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, require_role
from app.models.users import RoleEnum, User
from app.schemas.import_documents import DocumentDownloadResponse
from app.services import import_documents as document_service
from app.services.storage import import_documents as import_doc_storage_service

router = APIRouter(prefix="/import_documents", tags=["imports"])

ALLOWED_ROLES = [RoleEnum.convenor, RoleEnum.admin]


@router.get("/{document_id}", response_model=DocumentDownloadResponse, status_code=status.HTTP_200_OK)
def download_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    # was get_current_user, which lets through anyone holding a valid token,
    # an unapproved signup (role is None) included. This hands back a signed
    # URL to the raw sheet, which carries every applicant's id, contact
    # details and birth date, so it needs a real role behind it.
    actor: User = Depends(require_role(*ALLOWED_ROLES))
):
    document = document_service.get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document does not exist")
    signed_url = import_doc_storage_service.get_signed_url(document.storage_key)

    if signed_url is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Download link not created")
    return { 
        "original_file_name": document.original_file_name,
        "signed_url": signed_url,
        "content_type": document.content_type
    }

