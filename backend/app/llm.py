import json
from typing import Any, Dict, List, Tuple

from anthropic import Anthropic
from openai import OpenAI
from tenacity import RetryError, retry, retry_if_exception, stop_after_attempt, wait_exponential

from .config import get_settings
from .prompts import SYSTEM_PROMPT, build_context_block, build_user_prompt


def _is_retryable(exc: Exception) -> bool:
  message = str(exc).lower()
  return "rate limit" in message or "429" in message or "500" in message or "503" in message


def _retry_decorator():
  return retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
  )


def _get_openai_client() -> OpenAI:
  settings = get_settings()
  return OpenAI(api_key=settings.openai_api_key)


def _get_anthropic_client() -> Anthropic:
  settings = get_settings()
  if not settings.anthropic_api_key:
    raise RuntimeError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
  return Anthropic(api_key=settings.anthropic_api_key)


@_retry_decorator()
def _call_openai(system_prompt: str, user_prompt: str) -> str:
  settings = get_settings()
  client = _get_openai_client()
  resp = client.chat.completions.create(
    model=settings.openai_chat_model,
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt},
    ],
    temperature=0.0,
  )
  return resp.choices[0].message.content or ""


@_retry_decorator()
def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
  settings = get_settings()
  client = _get_anthropic_client()
  resp = client.messages.create(
    model=settings.anthropic_chat_model,
    max_tokens=1024,
    temperature=0.0,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}],
  )
  # Anthropic response content is a list of blocks; we expect a single text block.
  if not resp.content:
    return ""
  blocks = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
  return "".join(blocks)


def _parse_answer(raw: str) -> Dict[str, Any]:
  raw = raw.strip()
  # Try to find a JSON object within the response if there is extra text.
  start = raw.find("{")
  end = raw.rfind("}")
  if start != -1 and end != -1 and end > start:
    raw = raw[start : end + 1]

  try:
    data = json.loads(raw)
  except json.JSONDecodeError:
    return {"answer": raw, "citations": []}

  answer = str(data.get("answer", "")).strip()
  citations = data.get("citations") or []
  normalized_citations: List[Dict[str, str]] = []
  for c in citations:
    try:
      source = str(c.get("source", "")).strip()
      snippet = str(c.get("snippet", "")).strip()
      if source and snippet:
        normalized_citations.append({"source": source, "snippet": snippet})
    except Exception:
      continue

  return {"answer": answer, "citations": normalized_citations}


def generate_answer(question: str, retrieved: List[Tuple[str, str, float]]) -> Dict[str, Any]:
  """
  retrieved: list of (source, content, similarity)
  Returns dict with keys: answer (str), citations (list[dict]).
  """
  if not retrieved:
    return {
      "answer": "I don't know based on the provided context.",
      "citations": [],
    }

  context_block = build_context_block(retrieved)
  user_prompt = build_user_prompt(question, context_block)

  settings = get_settings()
  try:
    if settings.llm_provider == "anthropic":
      raw = _call_anthropic(SYSTEM_PROMPT, user_prompt)
    else:
      raw = _call_openai(SYSTEM_PROMPT, user_prompt)
  except RetryError as exc:
    # Unwrap last attempt error if present.
    last_exc = exc.last_attempt.exception() if exc.last_attempt else exc
    raise last_exc  # Let FastAPI error handler manage it.

  return _parse_answer(raw)

