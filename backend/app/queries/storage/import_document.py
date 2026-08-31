import uuid

from app.models.import_runs import SourceType
from app.queries.storage.supabase import get_supabase_client

BUCKET = "import_documents"


def upload_documents(
    content: bytes, content_type: str, extension: str, import_type: SourceType
):

    filename = f"{uuid.uuid4()}{extension}"
    storage_path = f"{import_type.value}/{filename}"
    get_supabase_client().storage.from_(BUCKET).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": content_type, "upsert": "false"},
    )
    return storage_path


def delete_document(storage_key: str) -> None:
    get_supabase_client().storage.from_(BUCKET).remove([storage_key])


def generate_signed_url(storage_key: str) -> str | None:
    return (
        get_supabase_client()
        .storage.from_(BUCKET)
        .create_signed_url(
            storage_key,
            300,  # link is only valid for 5 minutes
        )
        .get("signedURL")
    )
