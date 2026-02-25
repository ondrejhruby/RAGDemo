"use client";

import { useState } from "react";
import type { Citation } from "../lib/api";
import { ingestDoc, queryRag } from "../lib/api";

type Status = { type: "idle" } | { type: "loading"; label: string } | { type: "success"; message: string } | { type: "error"; message: string };

export default function HomePage() {
  const [source, setSource] = useState("");
  const [docText, setDocText] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);

  const [status, setStatus] = useState<Status>({ type: "idle" });

  const [topK, setTopK] = useState<number>(5);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    if (!source.trim() || !docText.trim()) {
      setStatus({ type: "error", message: "Source and document text are required." });
      return;
    }
    setStatus({ type: "loading", label: "Ingesting document..." });
    try {
      const res = await ingestDoc({ source: source.trim(), text: docText });
      setStatus({
        type: "success",
        message: `Ingested ${res.chunks_count} chunks (request ${res.request_id}).`,
      });
    } catch (err: any) {
      setStatus({
        type: "error",
        message: err?.message ?? "Failed to ingest document.",
      });
    }
  }

  async function handleQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) {
      setStatus({ type: "error", message: "Question is required." });
      return;
    }
    setStatus({ type: "loading", label: "Querying RAG backend..." });
    setAnswer(null);
    setCitations([]);
    try {
      const res = await queryRag({ question: question.trim(), top_k: topK });
      setAnswer(res.answer);
      setCitations(res.citations ?? []);
      setStatus({
        type: "success",
        message: `Answered (request ${res.request_id}).`,
      });
    } catch (err: any) {
      setStatus({
        type: "error",
        message: err?.message ?? "Failed to query.",
      });
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-400">
          Paste docs on the left, ask questions on the right. Answers are
          constrained to Supabase vector context.
        </p>
        {status.type !== "idle" && (
          <div
            className={`rounded-full px-3 py-1 text-xs ${
              status.type === "loading"
                ? "bg-blue-950 text-blue-200"
                : status.type === "success"
                  ? "bg-emerald-950 text-emerald-200"
                  : "bg-red-950 text-red-200"
            }`}
          >
            {status.type === "loading"
              ? status.label
              : status.type === "success"
                ? status.message
                : status.message}
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Ingest panel */}
        <section className="card flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-slate-100">Ingest document</h2>
          <form onSubmit={handleIngest} className="flex flex-1 flex-col gap-3">
            <div>
              <label className="label" htmlFor="source">
                Source name
              </label>
              <input
                id="source"
                className="input"
                placeholder="e.g. product_docs_v1"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              />
            </div>
            <div className="flex-1">
              <label className="label" htmlFor="doctext">
                Document text
              </label>
              <textarea
                id="doctext"
                className="input h-48 resize-y"
                placeholder="Paste any reference text here..."
                value={docText}
                onChange={(e) => setDocText(e.target.value)}
              />
            </div>
            <div className="mt-auto flex justify-end">
              <button
                type="submit"
                className="button-primary"
                disabled={status.type === "loading"}
              >
                Ingest
              </button>
            </div>
          </form>
        </section>

        {/* Query panel */}
        <section className="card flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-slate-100">Ask a question</h2>
          <form onSubmit={handleQuery} className="flex flex-col gap-3">
            <div>
              <label className="label" htmlFor="question">
                Question
              </label>
              <input
                id="question"
                className="input"
                placeholder="What does the document say about X?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="label mb-0" htmlFor="topk">
                top_k
              </label>
              <input
                id="topk"
                type="number"
                min={1}
                max={50}
                className="input max-w-[96px]"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value) || 5)}
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="button-primary"
                disabled={status.type === "loading"}
              >
                Ask
              </button>
            </div>
          </form>

          <div className="mt-3 space-y-3">
            <div>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Answer
              </h3>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-100">
                {answer ?? <span className="text-slate-500">No answer yet.</span>}
              </div>
            </div>

            <div>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Citations
              </h3>
              {citations.length === 0 ? (
                <p className="text-sm text-slate-500">No citations yet.</p>
              ) : (
                <ul className="space-y-2">
                  {citations.map((c, idx) => (
                    <li
                      key={`${c.source}-${idx}`}
                      className="rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                    >
                      <div className="mb-1 text-xs font-semibold text-slate-300">
                        {c.source}
                      </div>
                      <p className="text-xs text-slate-200 whitespace-pre-wrap">
                        {c.snippet}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

