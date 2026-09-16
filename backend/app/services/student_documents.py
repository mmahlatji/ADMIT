import uuid

from sqlalchemy.orm import Session

from app.models.student_documents import StudentDocument
from app.queries import student_documents as student_doc_queries


def get_document_by_hash(
    db: Session, applicant_id: uuid.UUID, sha256_hash: str
) -> StudentDocument | None:
    return student_doc_queries.get_student_documents_by_hash(db, applicant_id, sha256_hash)


def get_document_by_id(db: Session, document_id: uuid.UUID) -> StudentDocument | None:
    return student_doc_queries.get_student_document_by_id(db, document_id)


def create_document(
    db: Session,
    applicant_id: uuid.UUID,
    storage_key: str,
    original_file_name: str,
    content_type: str,
    sha256_hash: str,
) -> StudentDocument:
    return student_doc_queries.create_student_document(
        db,
        applicant_id,
        storage_key,
        original_file_name,
        content_type,
        sha256_hash,
    )
