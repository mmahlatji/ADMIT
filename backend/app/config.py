"""Application settings, loaded from environment / .env.

The backend owns all secrets; the frontend never sees these values —
it only ever talks to Supabase for auth and to us for everything else.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Hosted Supabase Postgres in normal use; a local postgres:16 container
    # is used by the data-layer owner to test Alembic migrations before
    # pushing them to hosted Supabase.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/admit"

    # Supabase project — used to verify auth JWTs issued to the frontend.
    supabase_url: str = ""
    supabase_jwt_secret: str = ""

    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
