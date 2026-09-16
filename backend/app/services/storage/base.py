"""Shared document-upload pipeline used by every document bucket."""

import hashlib
from typing import Protocol, TypeVar

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.queries.storage import bucket as storage
from app.services.storage.exceptions import (
    FileEmptyException,
    FileNotAllowedException,
    FileTooLargeException,
    FileUploadFailedException,
)

DocumentT = TypeVar("DocumentT")

MAX_FILE_SIZE = 1_000_000

# Canonical content types served/stored for each allowed extension. The value
# the client sends in the multipart header is ignored: it is as spoofable as
# the filename.
CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
}

# The PDF header may be offset by up to 1024 bytes per the spec.
_PDF_HEADER_SCAN_BYTES = 1024


def _is_text(content: bytes) -> bool:
    """Best-effort text sniff for CSV, which has no magic bytes."""
    if b"\x00" in content:
        return False
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def detect_extension(content: bytes) -> str | None:
    """Return the canonical extension matching ``content``, or None.

    Identifies a file by its content rather than its client-supplied filename,
    so a file can't masquerade as an allowed type just by being renamed. CSV
    has no signature and falls back to a text check (see ``_is_text``).
    """
    if b"%PDF-" in content[:_PDF_HEADER_SCAN_BYTES]:
        return ".pdf"
    if content[:4] == b"PK\x03\x04" and b"[Content_Types].xml" in content:
        return ".xlsx"
    if _is_text(content):
        return ".csv"
    return None


class DocumentStorageService(Protocol[DocumentT]):
    """Per-kind configuration for storing one type of document.

    ``build_storage_key`` decides the object path, ``get_by_hash``/``create``
    bind the DB record, and ``on_duplicate`` encodes the dedup semantics (re-point,
    reject, overwrite, ...).
    """

    bucket: str

    def build_storage_key(self, extension: str) -> str: ...

    def get_by_hash(self, db: Session, sha256_hash: str) -> DocumentT | None: ...

    def on_duplicate(self, db: Session, existing: DocumentT) -> DocumentT: ...

    def create(
        self,
        db: Session,
        *,
        storage_key: str,
        sha256_hash: str,
        original_file_name: str,
        content_type: str,
    ) -> DocumentT: ...


async def read_and_validate(
    file: UploadFile,
    allowed_extensions: frozenset[str],
    max_file_size: int = MAX_FILE_SIZE,
) -> tuple[bytes, str]:
    """Read an upload and confirm its content is an allowed type.

    Returns ``(content, extension)`` where ``extension`` is the canonical
    extension detected from the bytes. Raises ``FileEmptyException``,
    ``FileTooLargeException`` or ``FileNotAllowedException`` otherwise.
    """
    content = await file.read()

    if not content:
        raise FileEmptyException("File is empty")

    if len(content) > max_file_size:
        raise FileTooLargeException("File is too large")

    extension = detect_extension(content)
    if extension is None or extension not in allowed_extensions:
        raise FileNotAllowedException("File is not in allowed types")

    return content, extension


async def upload_document(
    db: Session,
    service: DocumentStorageService[DocumentT],
    content: bytes,
    extension: str,
    original_file_name: str | None,
) -> DocumentT:
    """Dedup, upload and record already-validated content."""
    file_hash = hashlib.sha256(content).hexdigest()

    existing = service.get_by_hash(db, file_hash)
    if existing is not None:
        return service.on_duplicate(db, existing)

    content_type = CONTENT_TYPES[extension]
    original_file_name = original_file_name or f"document{extension}"
    storage_key = service.build_storage_key(extension)

    try:
        # Offloaded to a threadpool: this is a synchronous network call to
        # Supabase Storage's HTTP API - running it inline on the event loop
        # blocks every other request for however long the upload takes.
        await run_in_threadpool(
            storage.upload_file,
            service.bucket,
            content,
            content_type,
            storage_key,
        )
    except Exception as exc:
        print(f"UPLOAD FAILED: {type(exc).__name__}: {exc}")
        raise FileUploadFailedException(
            f"Could not upload file {original_file_name}"
        ) from exc

    try:
        return service.create(
            db,
            storage_key=storage_key,
            sha256_hash=file_hash,
            original_file_name=original_file_name,
            content_type=content_type,
        )
    except Exception:
        # Storage succeeded but DB failed: remove the orphaned object.
        await run_in_threadpool(storage.delete_file, service.bucket, storage_key)
        raise


def get_signed_url(bucket: str, storage_key: str, expires_in: int = 300) -> str | None:
    """Return a short-lived download link for an object in a bucket."""
    return storage.generate_signed_url(bucket, storage_key, expires_in)
