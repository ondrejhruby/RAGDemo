import logging
import time
import uuid
from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .chunking import chunk_text
from .config import Settings, get_settings
from .embeddings import embed_query, embed_texts
from .llm import generate_answer
from .models import (
  HealthResponse,
  IngestRequest,
  IngestResponse,
  QueryRequest,
  QueryResponse,
)
from .vector_store import insert_chunks, similarity_search


logger = logging.getLogger("ragdemo")
logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
  app = FastAPI(title="Vector DB RAG Demo")

  # CORS for local dev; in real prod, tighten this.
  app.add_middleware(
    CORSMiddleware,
    allow_origins=[
      "http://localhost:3000",
      "http://127.0.0.1:3000",
       "localhost:3000",
      "127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  @app.middleware("http")
  async def add_request_id_and_logging(
    request: Request, call_next: Callable
  ) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start = time.monotonic()
    try:
      response = await call_next(request)
    except Exception as exc:
      duration_ms = (time.monotonic() - start) * 1000
      logger.exception(
        "request failed",
        extra={
          "request_id": request_id,
          "path": request.url.path,
          "method": request.method,
          "duration_ms": duration_ms,
        },
      )
      raise exc

    duration_ms = (time.monotonic() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
      "request completed",
      extra={
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
      },
    )
    return response

  @app.exception_handler(Exception)
  async def unhandled_exception_handler(
    request: Request, exc: Exception
  ) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    logger.exception("unhandled error", extra={"request_id": request_id})
    return JSONResponse(
      status_code=500,
      content={
        "detail": "Internal server error",
        "request_id": request_id,
      },
    )

  @app.get("/health", response_model=HealthResponse)
  async def health() -> HealthResponse:
    return HealthResponse(status="ok")

  @app.post("/ingest", response_model=IngestResponse)
  async def ingest(
    payload: IngestRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
  ) -> IngestResponse:
    request_id = x_request_id or getattr(request.state, "request_id", None) or str(
      uuid.uuid4()
    )

    text = payload.text.strip()
    if not text:
      raise HTTPException(status_code=400, detail="text must not be empty")

    chunks = chunk_text(text)
    if not chunks:
      raise HTTPException(status_code=400, detail="no chunks produced from text")

    logger.info(
      "ingest start",
      extra={
        "request_id": request_id,
        "source": payload.source,
        "chunks_count": len(chunks),
      },
    )

    embeddings = embed_texts(chunks)
    inserted = insert_chunks(payload.source, chunks, embeddings)

    logger.info(
      "ingest complete",
      extra={
        "request_id": request_id,
        "source": payload.source,
        "chunks_inserted": inserted,
      },
    )

    return IngestResponse(
      source=payload.source,
      chunks_count=inserted,
      request_id=request_id,
    )

  @app.post("/query", response_model=QueryResponse)
  async def query(
    payload: QueryRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
  ) -> QueryResponse:
    request_id = x_request_id or getattr(request.state, "request_id", None) or str(
      uuid.uuid4()
    )

    question = payload.question.strip()
    if not question:
      raise HTTPException(status_code=400, detail="question must not be empty")

    top_k = payload.top_k or settings.top_k

    logger.info(
      "query start",
      extra={
        "request_id": request_id,
        "top_k": top_k,
      },
    )

    q_embedding = embed_query(question)
    retrieved = similarity_search(q_embedding, top_k)

    logger.info(
      "retrieval complete",
      extra={
        "request_id": request_id,
        "retrieved_count": len(retrieved),
      },
    )

    answer_obj = generate_answer(question, retrieved)

    logger.info(
      "llm complete",
      extra={
        "request_id": request_id,
        "has_answer": bool(answer_obj.get("answer")),
        "citations_count": len(answer_obj.get("citations") or []),
      },
    )

    return QueryResponse(
      answer=str(answer_obj.get("answer", "")),
      citations=answer_obj.get("citations") or [],
      request_id=request_id,
    )

  return app


app = create_app()

