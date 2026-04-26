import type { GraphData, HealthLintResponse, QueryResponse, RefactorResponse, StatsResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    const raw = await res.text();
    if (raw) {
      try {
        const data = JSON.parse(raw);
        msg = data?.detail ?? data?.message ?? raw;
      } catch {
        msg = raw;
      }
    }
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

export const api = {
  graph: () => fetchJson<GraphData>("/graph"),
  stats: () => fetchJson<StatsResponse>("/stats"),
  query: (question: string) =>
    fetchJson<QueryResponse>("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
  refactor: () => fetchJson<RefactorResponse>("/refactor", { method: "POST" }),
  ingestText: (text: string) =>
    fetchJson<{ status: string; raw_note: string }>("/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, filename_hint: "manual-note.txt" }),
    }),
  uploadSingle: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetchJson<{ status: string; raw_note: string }>("/ingest/upload", { method: "POST", body: fd });
  },
  uploadBatch: (files: File[]) => {
    const fd = new FormData();
    files.forEach((file) => fd.append("files", file));
    return fetchJson<{ successes: Array<{ file: string; raw_note: string }>; errors: Array<{ file: string; error: string }> }>(
      "/ingest/upload/batch",
      {
      method: "POST",
      body: fd,
      },
    );
  },
  generateAll: () => fetchJson<{ generated: unknown[]; errors: string[] }>("/generate", { method: "POST" }),
  generateFromRaw: (raw_note_filenames: string[]) =>
    fetchJson<{ generated: unknown[]; errors: string[] }>("/generate/from-raw", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_note_filenames }),
    }),
  runHealthLint: () => fetchJson<HealthLintResponse>("/lint/health", { method: "POST" }),
  getLatestHealthLint: () => fetchJson<HealthLintResponse>("/lint/health/latest"),
};
