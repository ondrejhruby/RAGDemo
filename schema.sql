create extension if not exists vector;

create table if not exists documents (
  id bigserial primary key,
  source text not null,
  content text not null,
  embedding vector(1536),
  created_at timestamptz default now()
);

create index if not exists documents_embedding_ivfflat_idx
  on documents
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Optional: helper function for Supabase RPC-based similarity search.
create or replace function match_documents (
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id bigint,
  source text,
  content text,
  similarity float
)
language sql
stable
as $$
  select
    d.id,
    d.source,
    d.content,
    1 - (d.embedding <=> query_embedding) as similarity
  from documents d
  where d.embedding is not null
  order by d.embedding <=> query_embedding
  limit match_count;
$$;

