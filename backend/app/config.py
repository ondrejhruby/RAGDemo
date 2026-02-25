from functools import lru_cache
from typing import Literal, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  # Supabase
  supabase_url: AnyHttpUrl = Field(alias="SUPABASE_URL")
  supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")

  # OpenAI / Anthropic
  openai_api_key: str = Field(alias="OPENAI_API_KEY")
  anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")

  llm_provider: Literal["openai", "anthropic"] = Field(
    default="openai", alias="LLM_PROVIDER"
  )
  openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
  anthropic_chat_model: str = Field(
    default="claude-sonnet-4-6", alias="ANTHROPIC_CHAT_MODEL"
  )

  # Embeddings / retrieval
  chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
  chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
  top_k: int = Field(default=5, alias="TOP_K")

  # Guardrails
  max_context_chars: int = Field(default=4000, alias="MAX_CONTEXT_CHARS")

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings()  # type: ignore[call-arg]

