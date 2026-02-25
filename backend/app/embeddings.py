from typing import List

from openai import OpenAI

from .config import get_settings


_EMBED_MODEL = "text-embedding-3-small"


def _get_client() -> OpenAI:
  settings = get_settings()
  return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: List[str]) -> List[List[float]]:
  if not texts:
    return []

  client = _get_client()
  response = client.embeddings.create(model=_EMBED_MODEL, input=texts)
  return [item.embedding for item in response.data]


def embed_query(query: str) -> List[float]:
  vectors = embed_texts([query])
  return vectors[0]

