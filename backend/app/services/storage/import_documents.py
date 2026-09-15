import hashlib
from pathlib import Path

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.models.import_documents import Document
from app.models.import_runs import ImportRun, ImportStatus
from app.queries.import_documents import update_import_document as import_doc_queries_update
from app.queries.storage import import_document as import_queries
from app.services import import_documents as import_doc_queries
from app.services import import_runs as import_run_queries
from app.services.storage.exceptions import (
    FileAlreadyExistsException,
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
    FileUploadFailedException,
)

MAX_FILE_SIZE = 1_000_000  # 1 million bytes

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
    extension = Path(file.filename).suffix.lower()

    content = await file.read()

    if not content:
        raise FileEmptyException("File is empty")

    if len(content) > MAX_FILE_SIZE:
        raise FileTooLargeException("File is too large")

    if extension not in ALLOWED_FILE_TYPES:
        raise FileNotAllowedException("File is not in allowed types")

    # hash
    file_hash = hashlib.sha256(content).hexdigest()

    # check if document already exists
    existing_document = import_doc_queries.get_document_by_hash(db, file_hash)
    if existing_document is not None:
        # Only a run that actually succeeded should block re-uploading the same
        # file. Blocking on the hash alone meant a FAILED import could never be
        # retried: you would fix the cause and then be told the document had
        # already been uploaded, with no way through short of editing the file.
        prior_run = import_run_queries.get_import_run_by_id(
            db, existing_document.import_run_id
        )
        if prior_run is not None and prior_run.status is not ImportStatus.FAILED:
            raise FileAlreadyExistsException("Document has already been uploaded")

        # The bytes are identical, so the object already in storage is still
        # good. Re-point the document at this run rather than uploading a
        # second copy or breaking the unique hash constraint.
        return import_doc_queries_update(
            db, existing_document, import_run_id=import_run.import_run_id
        )

    try:
        # upload the document
        # offloaded to a threadpool: this is a synchronous network call to
        # Supabase Storage's HTTP API - running it inline on the event loop
        # blocks every other request (including unrelated ones like
        # /users/me) for however long the upload takes, or hangs forever if
        # the network call stalls.
        storage_key = await run_in_threadpool(
            import_queries.upload_documents,
            content,
            file.content_type,
            extension,
            import_run.source_type,
        )
    # Deliberately broad: this wraps a third-party HTTP call and every way it
    # can fail means the same thing to the caller. Chaining with `from exc`
    # keeps the original cause on the traceback instead of discarding it.
    except Exception as exc:
        print(f"UPLOAD FAILED: {type(exc).__name__}: {exc}")
        raise FileUploadFailedException(f"Could not upload file {file.filename}") from exc

    try:
        document = import_doc_queries.create_document(
            db,
            import_run_id=import_run.import_run_id,
            storage_key=storage_key,
            sha256_hash=file_hash,
            original_file_name=file.filename,
            content_type=file.content_type,
        )

    except Exception:
        # Storage succeeded but DB failed.
        # Remove the orphaned file. Offloaded for the same reason as above.
        await run_in_threadpool(import_queries.delete_document, storage_key)
        raise

    return document


def get_signed_url(storage_key: str):
    return import_queries.generate_signed_url(storage_key)
