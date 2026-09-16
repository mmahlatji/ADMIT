"""Storage service for import-run documents (uploaded source spreadsheets)."""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.import_documents import Document
from app.models.import_runs import ImportRun, ImportStatus
from app.queries.import_documents import update_import_document
from app.services import import_documents as import_doc_service
from app.services import import_runs as import_run_service
from app.services.storage import base
from app.services.storage.exceptions import FileAlreadyExistsException

IMPORT_DOCUMENTS_BUCKET = "import_documents"
IMPORT_DOCUMENTS_SIGNED_URL_EXPIRY = 300
IMPORT_DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".xlsx", ".csv"})


@dataclass
class ImportDocumentStorageService:
    """Storage config for import-run documents."""

    import_run: ImportRun
    bucket: str = IMPORT_DOCUMENTS_BUCKET

    def build_storage_key(self, extension: str) -> str:
        return f"{self.import_run.source_type.value}/{uuid.uuid4()}{extension}"

    def get_by_hash(self, db: Session, sha256_hash: str) -> Document | None:
        return import_doc_service.get_document_by_hash(db, sha256_hash)

    def on_duplicate(self, db: Session, existing: Document) -> Document:
        # Only a run that actually succeeded should block re-uploading the same
        # file. Blocking on the hash alone meant a FAILED import could never be
        # retried: you would fix the cause and then be told the document had
        # already been uploaded, with no way through short of editing the file.
        prior_run = import_run_service.get_import_run_by_id(db, existing.import_run_id)
        if prior_run is not None and prior_run.status is not ImportStatus.FAILED:
            raise FileAlreadyExistsException("Document has already been uploaded")

        # The bytes are identical, so the object already in storage is still
        # good. Re-point the document at this run rather than uploading a
        # second copy or breaking the unique hash constraint.
        return update_import_document(db, existing, import_run_id=self.import_run.import_run_id)

    def create(
        self,
        db: Session,
        *,
        storage_key: str,
        sha256_hash: str,
        original_file_name: str,
        content_type: str,
    ) -> Document:
        return import_doc_service.create_document(
            db,
            self.import_run.import_run_id,
            storage_key,
            original_file_name,
            content_type,
            sha256_hash,
        )


async def upload_document(
    db: Session,
    import_run: ImportRun,
    content: bytes,
    extension: str,
    original_file_name: str | None,
) -> Document:
    return await base.upload_document(
        db, ImportDocumentStorageService(import_run), content, extension, original_file_name
    )


def get_signed_url(storage_key: str) -> str | None:
    return base.get_signed_url(IMPORT_DOCUMENTS_BUCKET, storage_key, IMPORT_DOCUMENTS_SIGNED_URL_EXPIRY)
