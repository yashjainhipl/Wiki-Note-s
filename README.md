# Wiki Notes

**Python FastAPI OpenAI TypeScript React Vite JavaScript HTML5 CSS3 D3.js**

A self-evolving knowledge system that transforms raw data into a structured, continuously improving knowledge graph.

Wiki Notes is not a chatbot. It is a system that learns, restructures, and improves its own knowledge over time.

## Why this matters

Most production AI systems answer; they do not evolve an owned knowledge artifact. Wiki Notes is built so the wiki and graph can improve with use: write-back, refactor, and schema-bound pages. Tomorrow's retrieval runs on structure that changed on purpose, not only on new chat logs.

That is an intentional move from stateless retrieval (pull chunks, answer, move on) toward persistent intelligence: inspectable wiki pages, provenance, refactors, and a corpus that can compound instead of resetting every session.

Wiki Notes is an AI-powered knowledge platform inspired by Andrej Karpathy's "LLM Wiki" direction: treat documents as fuel for a living wiki and graph, not as disposable chunks for one-off retrieval.

## Screenshots and demos

### Knowledge graph
Wiki Notes knowledge graph: force-directed layout, clusters, and links

### Query and write-back
Wiki Notes query bar, answer, and graph context

### Ingest
Wiki Notes document upload and batch ingest UI

### Demo walkthrough (GIF)
Screen recording: ingest, generate, query, graph updates, refactor

## Problem statement

Traditional RAG pipelines typically:

- Retrieve raw document fragments at query time, with limited structure shared across sessions.
- Do not compound learning: the index may be static; answers do not systematically refine what the system "knows" for the next question.
- Repeat work: each query pays similar extraction and reasoning cost over the same material.

Core limitation: most systems retrieve; they do not refine a durable knowledge artifact. The corpus does not converge toward clearer pages, merged duplicates, or audited structure unless operators intervene manually.

Wiki Notes targets the gap: a write-back loop and background refactor so the knowledge base evolves, not just answers.

## Traditional RAG vs Wiki Notes

| Dimension | Traditional RAG | Wiki Notes |
| --- | --- | --- |
| What you ship | Retrieved passages + prompt | Structured wiki pages (Markdown + schema validation) plus a relationship graph |
| Memory model | Stateless per query (or opaque vectors) | Evolving on-disk knowledge with provenance and schema |
| Improvement | Same work each time unless the index changes | Compounding: confident answers write back; refactor consolidates and rewrites |
| Operator view | Chunks and scores | Pages, links, lint, stats treated like product surface area |

## Solution overview

Wiki Notes turns heterogeneous inputs into schema-backed wiki pages (Markdown with structured sections). A knowledge graph emerges from relationships among titles, tags, and cross-references, not as a bolt-on diagram, but as a projection of the same structured state the query layer uses. The stack exposes natural-language query with optional wiki updates when the model is sufficiently confident.

A refactor agent runs on demand to merge near-duplicate pages, repair weak summaries, batch-rewrite stale content, and keep the graph coherent.

End-to-end flow:

`raw -> parse -> wiki -> graph -> query -> write-back -> refactor -> improved knowledge`

- **Raw:** uploaded files or notes (multi-format ingestion, normalized to text).
- **Parse:** format-specific extractors produce clean text for downstream LLM steps.
- **Wiki:** the LLM structures and organizes raw text into validated wiki pages and merges updates against schema.
- **Graph:** nodes and links emerge from shared tags and related topics.
- **Query:** user questions retrieve relevant pages; the LLM answers with calibrated confidence.
- **Write-back:** high-confidence answers update or create wiki pages with provenance markers.
- **Refactor:** consolidation, rewriting, and lint-driven repair improve global quality.

## Architecture snapshot

`raw -> parse -> wiki -> graph -> query -> write-back -> refactor`

Each step produces a durable artifact, not a temporary computation.

## Key features

| Feature | What it does |
| --- | --- |
| Multi-format ingestion | Supports `.txt`, `.md`, `.pdf`, and `.docx`; text is extracted and stored as raw notes before structuring. |
| Automated wiki structuring | LLM structures raw notes into wiki pages (`title`, `summary`, `key_points`, `tags`, `related_topics`) with schema validation. |
| Query engine | Natural-language Q&A over wiki pages, returning answer plus graph-impact metadata. |
| Global wiki-agent prompt layer | A shared base instruction block is prepended to all LLM calls, while each workflow keeps task-specific schema prompts. |
| Self-improving write-back loop | Confidence-gated update/create path for wiki mutation (`WIKI_WRITEBACK_CONFIDENCE_THRESHOLD`). |
| Deep health lint (LLM) | `POST /lint/health` performs contradiction/staleness/orphan/missing-page analysis and writes timestamped reports. |
| Latest health report API | `GET /lint/health/latest` returns the newest persisted health report for UI summary cards. |
| Knowledge graph visualization | React UI renders graph with `react-force-graph-2d` + `d3-force` layout tuning. |
| Live graph updates | Pulse/birth cues and sync behavior after ingest, generate, query, and refactor. |
| Auto-tagging and clustering | Tag normalization and grouping behavior for coherent graph components. |
| Source traceability | `source_notes` provenance markers survive merges and rewrites. |
| Confidence filtering | Low-confidence outputs skip persistence to reduce graph drift risk. |
| Knowledge growth tracking | `GET /stats` exposes node/edge counts, recency, and tag distributions. |
| Modular LLM layer | Centralized async LLM calls and JSON-oriented prompts suitable for provider swaps. |
| Logging and observability | Structured logs across ingest, generate, query, refactor, and lint flows. |

## Advanced capabilities

- **Refactor agent (`POST /refactor`)**: duplicate detection via title similarity, merge unions (`key_points`, `tags`, `source_notes`), related-topic rewiring, and optional rewrite pass (`REFACTOR_REWRITE_MAX`).
- **Page consolidation**: near-duplicate pages merge into canonical artifacts with provenance retained.
- **Knowledge linting (`GET /lint`)**: rule-based checks over wiki pages; optional `suggest=true` can attach model hints.
- **Health linting (`POST /lint/health`)**: deeper LLM health checks with deterministic pre-signals (orphans/cross-ref candidates), batch analysis, and persisted reports.
- **Health lint retrieval (`GET /lint/health/latest`)**: fetches latest report for operational dashboards/UI.
- **Schema enforcement**: Pydantic models normalize and validate LLM output before persistence.
- **LLM output normalization guardrails**: health-lint pipeline coerces drifted model shapes into schema-compliant structures before final validation.
- **Knowledge rewriting**: full-page rewrites for weak/repetitive summaries during refactor.
- **Versioning snapshots**: optional disk snapshots in `backend/wiki_pages/_versions/` before destructive rewrites.

## System architecture

| Component | Responsibility |
| --- | --- |
| Ingestion layer | Upload endpoints, extension routing, size limits, persistence to raw notes. |
| Parsing layer | Pluggable extractors for plain text, Markdown, PDF, and DOCX. |
| Wiki structuring | Prompted LLM calls, output cleanup, page validation, provenance attachment. |
| Graph projection | Nodes + links derived from wiki page relationships (shared tags and related topics). |
| Query engine | Context page selection, model answer, confidence score, and wiki action metadata. |
| Health lint engine | Batch LLM + deterministic checks producing contradiction/staleness/gap reports under `health_reports/`. |
| Write-back loop | Updates or creates wiki pages when confidence exceeds threshold. |
| Refactor agent | Duplicate merges, rewrites weak pages, and repairs consistency issues. |

## Tech stack

- **Backend:** FastAPI, Uvicorn, Pydantic, python-dotenv, `pypdf`, python-docx, HTTPX/Ollama/OpenAI-compatible endpoints.
- **Frontend:** React 19, Vite, TypeScript, `react-force-graph-2d`, `d3-force`.
- **Storage:** filesystem Markdown wiki pages + raw note files (no separate DB in default setup).

## How it works (step-by-step)

1. Upload documents through UI/API; parser extracts and stores raw notes.
2. Generate wiki pages from raw notes; each note can become a validated structured page.
3. Build graph projection from titles, tags, and related topics via `GET /graph`.
4. Query in natural language; backend retrieves context and returns answer + metadata.
5. If confidence is high enough, write-back updates or creates wiki pages with provenance.
6. Run `POST /refactor` to merge duplicates and rewrite weak/stale pages.
7. Use `GET /lint` (optionally `suggest=true`) for fast structural checks.
8. Run `POST /lint/health` for deep semantic health analysis and review `GET /lint/health/latest`.

## System behavior

Wiki Notes behaves like a closed cognitive loop over your corpus:

- Learn from documents.
- Structure knowledge into schema-valid pages.
- Answer queries with explicit confidence and used-node evidence.
- Update selectively when trust is sufficient.
- Refactor and lint to keep the corpus healthy over time.

The graph UI is not decorative; it reflects the same relationship state the backend persists.

## Unique innovations

- **Self-improving loop:** answers can mutate durable knowledge, not just transient chat state.
- **Restructuring first:** refactor + lint make knowledge governance a first-class capability.
- **Explainable memory:** inspectable wiki pages with provenance, rather than opaque-only memory.
- **Continuous consolidation:** duplicates and weak pages are rewritten/merged toward stability.
- **Second-brain behavior:** structured summaries and links accumulate across sessions.

## What makes this hard

- **Consistency under change:** merges/rewrites must keep schema and references coherent.
- **Quality vs mutation:** confidence gates must prevent low-trust drift.
- **Rewrite vs stability:** aggressive edits can drift; conservative policy slows healing.
- **UI scale:** dense graphs require careful layout, clustering, and search support.

This project focuses as much on knowledge governance as on generation.

## Challenges and bottlenecks

| Challenge | Mitigation in Wiki Notes |
| --- | --- |
| High cost of initial structuring | Bounded concurrency (`GENERATE_CONCURRENCY`) and targeted generation paths. |
| Duplicate detection complexity | Tunable title similarity threshold (`CONSOLIDATION_STRING_THRESHOLD`) + provenance-preserving merges. |
| Noisy inputs | Parser warnings, schema normalization, and weak-page rewrite heuristics. |
| Graph clutter | `d3-force` collision/centering, search, visual grouping, and stats/lint feedback loops. |
| Rewrite over-modification | Confidence-gated write-back and budgeted refactor rewrites. |
| Schema consistency | Pydantic models and validation/repair pipeline before save. |
| Hallucination risk | Low-confidence skip, re-validation before persistence, optional snapshots. |

## Limitations

Wiki Notes is opinionated engineering, not magic:

- **Generation cost:** large corpus structuring is model-bound and token-expensive.
- **Duplicate detection limits:** title similarity can miss semantic overlap or over-merge when overtuned.
- **Rewrite imperfections:** model rewrites can smooth nuance or drift.
- **Retrieval mode:** default ranking is lexical-overlap heavy; semantic retrieval is future work.

## Testing and evaluation

Current evaluation has emphasized full-loop behavior over endpoint-only checks:

- Mixed-domain corpora with noisy notes and duplicate paths.
- Refactor before/after analysis of summary density, key-point diversity, tag coverage, edge evolution.
- Query mutation checks verifying low-confidence answers do not mutate wiki.
- Lint issue counts used as a regression signal.

Automated tests can be hardened further with `pytest` + `httpx` API integration suites.

## Demo / example flow

1. Upload PDFs/Markdown via ingest UI or `POST /ingest/upload/batch`.
2. Call `POST /generate/from-raw` (or `POST /generate`) to materialize wiki pages.
3. Open graph view and inspect nodes, links, and clusters.
4. Ask a query and verify `used_nodes` plus answer metadata.
5. Trigger high-confidence write-back and observe `wiki_action` updates.
6. Run `POST /refactor` and inspect merge/rewrite outcomes.
7. Optionally run `GET /lint?suggest=true` for guided cleanup.

## Key insight

A successful query is not just an answer; it can be a structural improvement to the system's knowledge. When confidence clears the threshold, the wiki absorbs grounded deltas, the graph tightens relationships, and future retrieval improves from durable changes.

Traditional stacks optimize the answer in the moment. Wiki Notes optimizes the corpus you carry forward.

## Before vs after refactor

| Before refactor | After refactor |
| --- | --- |
| Duplicate/near-duplicate pages | Canonical merged pages with `merged_from` provenance |
| Noisy or thin summaries | Tighter summaries + stronger key-point sets |
| Weak or accidental connectivity | Cleaner rewiring of relationships and tag-aligned links |

## Future improvements

- Semantic retrieval (dense or hybrid ranking).
- Knowledge-gap detection from query streams.
- Better node ranking (e.g., PageRank/temporal scoring in backend).
- Additional graph UI polish (presets, minimap, accessibility pass).
- Multi-user namespaces and per-tenant wiki roots.

## Quickstart

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

If needed, set `VITE_API_BASE` in `frontend/.env` (see `frontend/.env.example`).

## Project structure

- `backend/` - FastAPI app, routes, services, wiki/raw storage.
- `frontend/` - React + Vite client and graph UI.
- `backend/raw_notes/` - normalized input text artifacts.
- `backend/wiki_pages/` - structured wiki pages (`.md`, with legacy `.json` read support).
- `backend/wiki_pages/_versions/` - optional rewrite snapshots.
- `backend/wiki_pages/health_reports/` - persisted deep health-lint reports.

## Conclusion

Wiki Notes moves beyond one-shot RAG by treating structured knowledge as a mutable, versioned artifact that improves through query-driven updates and refactor. This is the shift from querying data to owning and evolving knowledge.

If you are evaluating the codebase, good starting points are:

- `backend/app/main.py` for route registration and app wiring.
- `backend/app/services` for wiki/query/refactor behavior.
- `frontend/src/components/KnowledgeGraph.tsx` for real-time graph reflection of system state.
