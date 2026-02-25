export type IngestRequest = {
  source: string;
  text: string;
};

export type IngestResponse = {
  source: string;
  chunks_count: number;
  request_id: string;
};

export type Citation = {
  source: string;
  snippet: string;
};

export type QueryRequest = {
  question: string;
  top_k?: number;
};

export type QueryResponse = {
  answer: string;
  citations: Citation[];
  request_id: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) {
        message = Array.isArray(data.detail)
          ? data.detail.map((d: any) => d.msg ?? String(d)).join(", ")
          : String(data.detail);
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function ingestDoc(body: IngestRequest): Promise<IngestResponse> {
  const res = await fetch(`${API_URL}/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return handleResponse<IngestResponse>(res);
}

export async function queryRag(body: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return handleResponse<QueryResponse>(res);
}

