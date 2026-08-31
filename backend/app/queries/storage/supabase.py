from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Build the Supabase object-storage client once, lazily, so a blank
    SUPABASE_URL doesn't crash imports."""
    return create_client(
        get_settings().supabase_url,
        get_settings().supabase_secret_key,
    )