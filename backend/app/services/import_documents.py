import uuid

from sqlalchemy.orm import Session

from app.models import Document
from app.queries import import_documents as import_doc_queries


def get_document_by_hash(db: Session, sha256_hash: str) -> Document | None:
    return import_doc_queries.get_import_documents_by_hash(db, sha256_hash)

def get_document_by_id(db: Session, document_id: uuid.UUID) -> Document | None:
    return import_doc_queries.get_import_document_by_id(db, document_id)


def create_document(
    db: Session,
    import_run_id: uuid.UUID,
    storage_key: str,
    original_file_name: str,
    content_type: str,
    sha256_hash: str   
):
    return import_doc_queries.create_import_document(
        db,
        import_run_id,
        storage_key,
        original_file_name,
        content_type,
        sha256_hash
    )



    