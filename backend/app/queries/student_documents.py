import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student_documents import StudentDocument


def get_student_document_by_id(db: Session, document_id: uuid.UUID) -> StudentDocument | None:
    """Look up a student document by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(StudentDocument).where(StudentDocument.document_id == document_id)
    ).scalar_one_or_none()


def get_student_documents(db: Session, skip: int = 0, limit: int = 100) -> list[StudentDocument]:
    """List student documents, paginated."""
    return list(db.execute(select(StudentDocument).offset(skip).order_by(StudentDocument.applicant_id.asc()).limit(limit)).scalars())


def create_student_document(
    db: Session,
    applicant_id: uuid.UUID,
    storage_key: str,
    original_file_name: str,
    content_type: str,
    sha256_hash: str,
) -> StudentDocument:
    """Insert a new student document row."""
    document = StudentDocument(
        document_id=uuid.uuid4(),
        applicant_id=applicant_id,
        storage_key=storage_key,
        original_file_name=original_file_name,
        content_type=content_type,
        sha256_hash=sha256_hash,
    )
    db.add(document)
    db.flush()
    db.refresh(document)
    return document


def update_student_document(
    db: Session,
    document: StudentDocument,
    applicant_id: uuid.UUID | None = None,
    storage_key: str | None = None,
    original_file_name: str | None = None,
    content_type: str | None = None,
    sha256_hash: str | None = None,
) -> StudentDocument:
    """Partially update a student document, only sets fields explicitly passed."""
    fields = {
        "applicant_id": applicant_id,
        "storage_key": storage_key,
        "original_file_name": original_file_name,
        "content_type": content_type,
        "sha256_hash": sha256_hash,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(document, field, value)
    db.flush()
    db.refresh(document)
    return document


def delete_student_document(db: Session, document: StudentDocument) -> None:
    """Delete a student document row."""
    db.delete(document)
    db.flush()
