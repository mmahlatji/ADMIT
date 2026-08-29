import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.import_documents import Document


def get_import_document_by_id(db: Session, document_id: uuid.UUID) -> Document | None:
    """Look up an import-run document by its id. Returns None if it doesn't exist yet."""
    return db.execute(
        select(Document).where(Document.document_id == document_id)
    ).scalar_one_or_none()


def get_import_documents(db: Session, skip: int = 0, limit: int = 100) -> list[Document]:
    """List import-run documents, paginated."""
    return list(db.execute(select(Document).offset(skip).order_by(Document.uploaded_at.desc()).limit(limit)).scalars())


def create_import_document(
    db: Session,
    import_run_id: uuid.UUID,
    storage_key: uuid.UUID,
    original_file_name: str,
    content_type: str,
    sha256_hash: str,
) -> Document:
    """Insert a new import-run document row."""
    document = Document(
        document_id=uuid.uuid4(),
        import_run_id=import_run_id,
        storage_key=storage_key,
        original_file_name=original_file_name,
        content_type=content_type,
        sha256_hash=sha256_hash,
    )
    db.add(document)
    db.flush()
    db.refresh(document)
    return document


def update_import_document(
    db: Session,
    document: Document,
    import_run_id: uuid.UUID | None = None,
    storage_key: uuid.UUID | None = None,
    original_file_name: str | None = None,
    content_type: str | None = None,
    sha256_hash: str | None = None,
) -> Document:
    """Partially update an import-run document, only sets fields explicitly passed."""
    fields = {
        "import_run_id": import_run_id,
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


def delete_import_document(db: Session, document: Document) -> None:
    """Delete an import-run document row."""
    db.delete(document)
    db.flush()
