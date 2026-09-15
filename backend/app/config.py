from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""

    # (TBD)
    supabase_url: str = ""
    supabase_secret_key: str = ""
    environment: str = "development"

    # Local Ollama serving the natural-language query model. Defaults to the
    # 4-bit (Q4_K_M) instruct tag; quantization is a property of the model file,
    # not the request.
    ollama_url: str = ""
    ollama_model: str = ""
    # Generous: CPU-only inference of the 7B model can take minutes per prompt.
    ollama_timeout_seconds: float = 600.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
