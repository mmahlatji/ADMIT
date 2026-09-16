"""Storage service for student documents (per-applicant uploads, e.g. transcripts)."""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.student_documents import StudentDocument
from app.services import student_documents as student_doc_service
from app.services.storage import base
from app.services.storage.exceptions import FileAlreadyExistsException

STUDENT_DOCUMENTS_BUCKET = "student_documents"
STUDENT_DOCUMENTS_SIGNED_URL_EXPIRY = 300
STUDENT_DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".pdf"})


@dataclass
class StudentDocumentStorageService:
    """Storage config for student documents."""

    applicant_id: uuid.UUID
    campus_id: str
    bucket: str = STUDENT_DOCUMENTS_BUCKET

    def build_storage_key(self, extension: str) -> str:
        return f"{self.campus_id}/{uuid.uuid4()}{extension}"

    def get_by_hash(self, db: Session, sha256_hash: str) -> StudentDocument | None:
        return student_doc_service.get_document_by_hash(db, self.applicant_id, sha256_hash)

    def on_duplicate(self, db: Session, existing: StudentDocument) -> StudentDocument:
        # Scoped to the applicant, so this really is the same applicant sending
        # the same file twice.
        raise FileAlreadyExistsException("Document has already been uploaded")

    def create(
        self,
        db: Session,
        *,
        storage_key: str,
        sha256_hash: str,
        original_file_name: str,
        content_type: str,
    ) -> StudentDocument:
        return student_doc_service.create_document(
            db,
            self.applicant_id,
            storage_key,
            original_file_name,
            content_type,
            sha256_hash,
        )


async def upload_document(
    db: Session,
    applicant_id: uuid.UUID,
    campus_id: str,
    content: bytes,
    extension: str,
    original_file_name: str | None,
) -> StudentDocument:
    return await base.upload_document(
        db,
        StudentDocumentStorageService(applicant_id, campus_id),
        content,
        extension,
        original_file_name,
    )


def get_signed_url(storage_key: str) -> str | None:
    return base.get_signed_url(
        STUDENT_DOCUMENTS_BUCKET, storage_key, STUDENT_DOCUMENTS_SIGNED_URL_EXPIRY
    )
