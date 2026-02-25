from typing import List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
  source: str = Field(..., min_length=1, max_length=256)
  text: str = Field(..., min_length=1)


class IngestResponse(BaseModel):
  source: str
  chunks_count: int
  request_id: str


class QueryRequest(BaseModel):
  question: str = Field(..., min_length=1)
  top_k: Optional[int] = Field(default=None, ge=1, le=50)


class Citation(BaseModel):
  source: str
  snippet: str


class QueryResponse(BaseModel):
  answer: str
  citations: List[Citation]
  request_id: str


class HealthResponse(BaseModel):
  status: str

