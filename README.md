## Vector DB RAG Demo

Minimal but production-shaped RAG example using:

- **Frontend**: Next.js (TypeScript) single-page UI
- **Backend**: FastAPI (Python) for ingestion, retrieval, and LLM calls
- **Vector DB**: Supabase Postgres with `pgvector`
- **LLMs**: OpenAI (`gpt-4o-mini`) by default, optional Anthropic (`claude-sonnet-4-6`)

The backend exposes `/ingest` and `/query` endpoints; the frontend lets you paste documents, ingest them into Supabase, and ask context-constrained questions.

---

### Project structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, /ingest + /query + /health
│   │   ├── config.py          # Settings from env vars (pydantic-settings)
│   │   ├── models.py          # Request/response models
│   │   ├── chunking.py        # Recursive text splitter
│   │   ├── embeddings.py      # OpenAI embeddings wrapper
│   │   ├── vector_store.py    # Supabase pgvector insert + similarity search
│   │   ├── llm.py             # OpenAI / Anthropic chat abstraction
│   │   └── prompts.py         # Prompt templates / context builder
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx           # Ingest + ask UI
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── src/lib/api.ts         # Typed fetch helpers for /ingest and /query
│   ├── package.json
│   ├── Dockerfile
│   ├── next.config.ts
│   └── tailwind.config.ts
├── schema.sql                 # Supabase table + index + match_documents()
├── docker-compose.yml
└── .env.example               # Root env template
```

---

### Database schema (Supabase)

Execute `schema.sql` in your Supabase SQL editor:

- Creates the `vector` extension
- Creates a `documents` table with `embedding vector(1536)`
- Adds an IVFFlat index on embeddings
- Defines a `match_documents(query_embedding, match_count)` helper for similarity search

---

### Configuration (.env)

Copy `.env.example` to `.env` at the repo root and fill in values:

```bash
cp .env.example .env
```

Key variables:

- **SUPABASE_URL**: Supabase project URL
- **SUPABASE_SERVICE_ROLE_KEY**: service role key (used server-side only)
- **OPENAI_API_KEY**: OpenAI API key
- **ANTHROPIC_API_KEY**: Anthropic API key (optional; required if `LLM_PROVIDER=anthropic`)
- **LLM_PROVIDER**: `openai` (default) or `anthropic`
- **OPENAI_CHAT_MODEL**: e.g. `gpt-4o-mini`
- **ANTHROPIC_CHAT_MODEL**: e.g. `claude-sonnet-4-6`
- **CHUNK_SIZE / CHUNK_OVERLAP**: recursive character splitter config
- **TOP_K**: default number of retrieved chunks

The frontend reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000` in `.env.example`).

---

### Running locally with Docker

Prerequisites:

- Supabase project with `pgvector` enabled
- `docker` and `docker compose`
- Valid OpenAI API key (and optionally Anthropic)

Steps:

1. **Apply DB schema in Supabase**

   - Open the Supabase SQL editor.
   - Paste the contents of `schema.sql`.
   - Run the script.

2. **Configure environment**

   ```bash
   cp .env.example .env
   # then edit .env to add your Supabase + OpenAI/Anthropic keys
   ```

3. **Install Dependencies**
    Backend:
    ```bash
    cd backend
    uv pip install -r requirements.txt
    ```
    Frontend (separate terminal):
    ```bash
    cd frotend
    pnpm install
    ```
4. **Start the app**
    3. **Install Dependencies**
    Backend:
    ```bash
    cd backend #If not already there
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    ```
    Frontend (separate terminal):
    ```bash
    cd frotend #If not already there
    pnpm run buil
    pnpm run start
    ```
3. **Alternate: Start the app with Docker (WIP)**

   ```bash
   docker compose up --build
   ```

   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`

---

### API endpoints

#### `POST /ingest`

- **Body**:

  ```json
  {
    "source": "product_docs_v1",
    "text": "Long document text to be chunked and embedded..."
  }
  ```

- **Response**:

  ```json
  {
    "source": "product_docs_v1",
    "chunks_count": 12,
    "request_id": "uuid-v4"
  }
  ```

- **Example curl**:

  ```bash
  curl -X POST http://localhost:8000/ingest \
    -H "Content-Type: application/json" \
    -d '{"source":"product_docs_v1","text":"Hello world"}'
  ```

#### `POST /query`

- **Body**:

  ```json
  {
    "question": "What does the document say about pricing?",
    "top_k": 5
  }
  ```

- **Response**:

  ```json
  {
    "answer": "The document says ...",
    "citations": [
      {
        "source": "product_docs_v1",
        "snippet": "Exact snippet from stored chunk..."
      }
    ],
    "request_id": "uuid-v4"
  }
  ```

- **Example curl**:

  ```bash
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"question":"What does the document say about pricing?","top_k":5}'
  ```

#### `GET /health`

- Returns:

  ```json
  { "status": "ok" }
  ```

---

### Reliability basics

- **Request IDs**
  - Every backend request gets a UUIDv4 `X-Request-ID` header.
  - Included in JSON responses (`request_id`) and structured logs.

- **Retries**
  - LLM calls (OpenAI and Anthropic) use exponential backoff with up to 3 attempts.
  - Retries trigger only for likely 429/5xx style errors.

- **Logging**
  - Key events logged with `request_id`, including:
    - ingest start/complete (chunk counts)
    - query start
    - retrieval complete (k, retrieved_count)
    - LLM complete (citations_count)
  - Request middleware logs path, method, status, and latency.

---

### Frontend UX

- **Ingest panel**
  - Source name input
  - Large textarea to paste document text
  - Ingest button, with status chip showing chunks count + request ID

- **Query panel**
  - Question input and configurable `top_k`
  - Answer box
  - Citations list with source labels and snippets

All questions are answered only from the retrieved context; if the answer is not in the context, the model is instructed to say it does not know.