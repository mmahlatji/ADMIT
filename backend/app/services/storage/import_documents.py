
import hashlib
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.import_documents import Document
from app.models.import_runs import ImportRun
from app.queries.storage import import_document as import_queries
from app.services import import_documents as import_doc_queries
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
    FileUploadFailedException,
)

MAX_FILE_SIZE = 1_000_000 # 1 million bytes

ALLOWED_FILE_TYPES = {
    ".xlsx",
    ".csv",
    ".pdf",
}


async def upload_document(
    db: Session,
    import_run: ImportRun,
    file: UploadFile,
) -> Document:
    extension = Path(
                file.filename
            ).suffix.lower()

    
    content = await file.read()

    if not content:
        raise FileEmptyException("File is empty")

    if len(content) > MAX_FILE_SIZE:
        raise FileTooLargeException("File is too large")

    if extension not in ALLOWED_FILE_TYPES:
        raise FileNotAllowedException("File is not in allowed types")

    # hash
    file_hash = hashlib.sha256(
        content
    ).hexdigest()

    # check if document already exists
    existing_document = import_doc_queries.get_document_by_hash(db, file_hash)
    if existing_document is not None:
        raise FileAlreadyExistsException("Document has already been uploaded")


    
    try:
        # upload the document
        storage_key = import_queries.upload_documents(
                content,
                file.content_type,
                extension,
                import_run.source_type
            )
    except Exception:
        raise FileUploadFailedException(f"Could not upload file {file.filename}")

    try:
        document = import_doc_queries.create_document(
            db,
            import_run_id = import_run.import_run_id,
            storage_key=storage_key,
            sha256_hash=file_hash,
            original_file_name=file.filename,
            content_type=file.content_type,
            )
        
    except Exception:
        # Storage succeeded but DB failed.
        # Remove the orphaned file.
        import_queries.delete_document(storage_key)
        raise

    return document


def get_signed_url(storage_key: str):
    return import_queries.generate_signed_url(storage_key)