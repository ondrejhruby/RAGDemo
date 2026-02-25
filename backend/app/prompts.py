from typing import List, Tuple

from .config import get_settings


SYSTEM_PROMPT = (
  "You are a question-answering assistant over a set of documents.\n"
  "Answer the user's question using ONLY the provided context.\n"
  "If the answer cannot be found in the context, say you don't know.\n"
  "Be concise and factual."
)


def build_context_block(chunks: List[Tuple[str, str, float]]) -> str:
  """
  chunks: list of (source, content, similarity)
  """
  settings = get_settings()

  lines: List[str] = []
  total_chars = 0

  for source, content, similarity in chunks:
    snippet = content.strip()
    if not snippet:
      continue

    block = f"[source: {source} | similarity: {similarity:.3f}]\n{snippet}\n"
    if total_chars + len(block) > settings.max_context_chars:
      break

    lines.append(block)
    total_chars += len(block)

  return "\n".join(lines)


def build_user_prompt(question: str, context_block: str) -> str:
  return (
    "Use the following context to answer the question.\n\n"
    "Context:\n"
    f"{context_block}\n\n"
    "Question:\n"
    f"{question}\n\n"
    "Provide a JSON object with the following shape exactly:\n"
    '{\"answer\": string, \"citations\": [{\"source\": string, \"snippet\": string}]}.\n'
    "If the context does not contain the answer, set \"answer\" to a brief\n"
    "statement that you don't know based on the context, and an empty citations array."
  )

