from typing import List, Sequence, Tuple

from supabase import Client, create_client

from .config import get_settings


def _get_client() -> Client:
  settings = get_settings()
  return create_client(str(settings.supabase_url), settings.supabase_service_role_key)


def insert_chunks(
  source: str, chunks: Sequence[str], embeddings: Sequence[Sequence[float]]
) -> int:
  if not chunks:
    return 0
  if len(chunks) != len(embeddings):
    raise ValueError("Number of chunks and embeddings must match")

  client = _get_client()
  rows = [
    {
      "source": source,
      "content": chunk,
      "embedding": embedding,
    }
    for chunk, embedding in zip(chunks, embeddings)
  ]
  client.table("documents").insert(rows).execute()
  return len(rows)


def similarity_search(
  query_embedding: Sequence[float], top_k: int
) -> List[Tuple[str, str, float]]:
  """
  Returns list of (source, content, similarity).
  """
  client = _get_client()
  query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

  resp = client.rpc(
    "match_documents",
    {
      "query_embedding": query_embedding_str,
      "match_count": top_k,
    },
  ).execute()

  data = resp.data or []

  results: List[Tuple[str, str, float]] = []
  for row in data:
    results.append(
      (
        row.get("source", ""),
        row.get("content", ""),
        float(row.get("similarity", 0.0)),
      )
    )
  return results

