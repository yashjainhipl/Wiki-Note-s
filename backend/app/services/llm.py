from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx
import ollama

from ..config import (
    LLM_FALLBACK_ENABLED,
    LLM_PROVIDER,
    LLM_STRICT_PRIMARY,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_ORGANIZATION,
    OPENAI_PROJECT,
)

_client: httpx.AsyncClient | None = None
_client_lock = asyncio.Lock()
_client_fingerprint: tuple[str, str, str, str] | None = None
logger = logging.getLogger(__name__)

GLOBAL_WIKI_AGENT_PROMPT = """# LLM Wiki Agent — Schema & Workflow Instructions

This wiki is maintained entirely by your coding agent. No API key or Python scripts needed — just open this repo in Codex, OpenCode, or any agent that reads this file, and talk to it.

## How to Use

Describe what you want in plain English:
- "Ingest this file: raw/papers/my-paper.md"
- "What does the wiki say about transformer models?"
- "Check the wiki for orphan pages and contradictions"
- "Build the knowledge graph"

Or use shorthand triggers:
- `ingest <file>` -> runs the Ingest Workflow
- `query: <question>` -> runs the Query Workflow
- `health` -> runs the Health Workflow (fast, every session)
- `lint` -> runs the Lint Workflow (expensive, periodic)
- `build graph` -> runs the Graph Workflow

## Directory Layout

raw/          # Immutable source documents — never modify these
wiki/         # Agent owns this layer entirely
  index.md    # Catalog of all pages — update on every ingest
  log.md      # Append-only chronological record
  overview.md # Living synthesis across all sources
  sources/    # One summary page per source document
  entities/   # People, companies, projects, products
  concepts/   # Ideas, frameworks, methods, theories
  syntheses/  # Saved query answers
graph/        # Auto-generated graph data
tools/        # Standalone Python scripts
  health.py   # Structural checks (deterministic, no LLM calls)
  lint.py     # Content quality checks (uses LLM for semantic analysis)
  build_graph.py  # Knowledge graph generation

## Page Format

Every wiki page uses this frontmatter:

---
title: "Page Title"
type: source | entity | concept | synthesis
tags: []
sources: []
last_updated: YYYY-MM-DD
---

Use [[PageName]] wikilinks to link to other wiki pages.

## Ingest Workflow

Triggered by: "ingest <file>"

Steps (in order):
1. Read the source document fully
2. Read wiki/index.md and wiki/overview.md for current wiki context
3. Write wiki/sources/<slug>.md
4. Update wiki/index.md
5. Update wiki/overview.md
6. Update/create entity pages for key people, companies, projects
7. Update/create concept pages for key ideas and frameworks
8. Flag any contradictions with existing wiki content
9. Append to wiki/log.md: ## [YYYY-MM-DD] ingest | <Title>
10. Post-ingest validation (broken links/index sync/summary)

## Query Workflow

Triggered by: "query: <question>"

Steps:
1. Read wiki/index.md to identify relevant pages
2. Read those pages
3. Synthesize answer with inline citations as [[PageName]] wikilinks
4. Ask user if answer should be saved under wiki/syntheses/<slug>.md

## Lint Workflow

Triggered by: "lint"

Check for orphans, broken links, contradictions, stale summaries, missing entity pages, sparse pages, and data gaps.

Graph-aware checks:
- Hub stubs
- Fragile bridges
- Isolated communities

Output lint report and ask whether to save to wiki/lint-report.md.

## Health Workflow

Triggered by: "health"

Run python tools/health.py (or --json).
Structural checks only (zero LLM calls): empty files, index sync, log coverage.

## Graph Workflow

Triggered by: "build graph"

First try: python tools/build_graph.py --open
Fallback manual process to create graph/graph.json and graph/graph.html.

## Naming Conventions

- Source slugs: kebab-case matching source filename
- Entity pages: TitleCase.md
- Concept pages: TitleCase.md

## Log Format

## [YYYY-MM-DD] <operation> | <title>
operations: ingest, query, health, lint, graph, report

## Hard Rules

HG-WA-01: Graph layer must not auto-create pages from broken links.
HG-WA-02: New slash commands must not duplicate existing command coverage.
"""


def compose_system_prompt(task_prompt: str) -> str:
    task_prompt = (task_prompt or "").strip()
    if not task_prompt:
        return GLOBAL_WIKI_AGENT_PROMPT
    return f"{GLOBAL_WIKI_AGENT_PROMPT}\n\n--- Task Context ---\n{task_prompt}"


async def get_async_openai_client() -> httpx.AsyncClient:
    global _client, _client_fingerprint
    fp = (
        OPENAI_API_KEY,
        OPENAI_BASE_URL.rstrip("/"),
        OPENAI_ORGANIZATION,
        OPENAI_PROJECT,
    )
    if _client is None or _client_fingerprint != fp:
        async with _client_lock:
            if _client is None or _client_fingerprint != fp:
                if _client is not None:
                    await _client.aclose()
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
                if OPENAI_ORGANIZATION:
                    headers["OpenAI-Organization"] = OPENAI_ORGANIZATION
                if OPENAI_PROJECT:
                    headers["OpenAI-Project"] = OPENAI_PROJECT
                _client = httpx.AsyncClient(
                    base_url=OPENAI_BASE_URL.rstrip("/"),
                    headers=headers,
                    timeout=90.0,
                )
                _client_fingerprint = fp
    return _client


async def close_async_openai_client() -> None:
    global _client, _client_fingerprint
    if _client is not None:
        await _client.aclose()
        _client = None
        _client_fingerprint = None


async def ask_json_via_openai(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable.")
    client = await get_async_openai_client()
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": compose_system_prompt(system_prompt)},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    resp = await client.post("/chat/completions", json=payload)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def _ollama_chat(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    return ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": compose_system_prompt(system_prompt)},
            {"role": "user", "content": user_prompt},
        ],
        format="json",
        options={"temperature": 0.2},
    )


async def ask_json_via_ollama(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    response = await asyncio.to_thread(_ollama_chat, system_prompt, user_prompt)
    content = response["message"]["content"]
    return json.loads(content)


async def ask_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    provider = LLM_PROVIDER
    if provider not in {"ollama", "openai", "auto"}:
        raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Use one of: ollama, openai, auto.")

    if provider == "openai":
        logger.info("llm provider=openai")
        return await ask_json_via_openai(system_prompt, user_prompt)

    try:
        logger.info("llm provider=ollama model=%s", OLLAMA_MODEL)
        return await ask_json_via_ollama(system_prompt, user_prompt)
    except Exception as exc:
        if LLM_STRICT_PRIMARY:
            logger.warning("llm provider=ollama strict_primary=true error=%s", exc)
            raise
        if not LLM_FALLBACK_ENABLED:
            logger.warning("llm provider=ollama fallback=false error=%s", exc)
            raise
        logger.warning("llm provider=ollama fallback=openai reason=%s", exc)
        return await ask_json_via_openai(system_prompt, user_prompt)

