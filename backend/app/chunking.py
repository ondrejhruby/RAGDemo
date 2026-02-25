from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import get_settings


def get_text_splitter() -> RecursiveCharacterTextSplitter:
  settings = get_settings()
  return RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=[
      "\n\n",
      "\n",
      ". ",
      "!",
      "?",
      ",",
      " ",
      "",
    ],
  )


def chunk_text(text: str) -> List[str]:
  splitter = get_text_splitter()
  return splitter.split_text(text)

