import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vector DB RAG Demo",
  description: "Minimal production-shaped RAG demo with Supabase, FastAPI, and Next.js.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-50 antialiased">
        <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6">
          <header className="mb-6 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                Vector DB RAG Demo
              </h1>
              <p className="text-sm text-slate-400">
                FastAPI + Supabase pgvector + Next.js
              </p>
            </div>
          </header>
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}

