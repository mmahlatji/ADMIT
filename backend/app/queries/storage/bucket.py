"""Low-level Supabase Storage object operations for document buckets.

The bucket is passed in by the caller, so these helpers stay reusable across import
documents, student documents, and any future bucket without duplication of logic.
"""

from app.queries.storage.supabase import get_supabase_client


def upload_file(bucket: str, content: bytes, content_type: str, storage_path: str) -> str:
    """Upload one object to ``bucket`` and return its storage key."""
    get_supabase_client().storage.from_(bucket).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": content_type, "upsert": "false"},
    )
    return storage_path


def delete_file(bucket: str, storage_key: str) -> None:
    """Remove one object from ``bucket`` by its storage key."""
    get_supabase_client().storage.from_(bucket).remove([storage_key])


def generate_signed_url(bucket: str, storage_key: str, expires_in: int = 300) -> str | None:
    """Return a short-lived download URL for an object, or None if it can't be made."""
    return (
        get_supabase_client()
        .storage.from_(bucket)
        .create_signed_url(storage_key, expires_in)
        .get("signedURL")
    )
