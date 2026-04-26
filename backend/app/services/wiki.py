from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..models import WikiPage
from .file_handler import load_wiki_page, save_wiki_page, wiki_path_for_title
from .llm import ask_json
from .tags import normalize_related_topics, normalize_tags
from .wiki_schema import validate_and_fix_wiki_page


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_json_or_fallback(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": data.get("title") or "Untitled",
        "summary": data.get("summary") or "",
        "key_points": data.get("key_points") or [],
        "tags": data.get("tags") or [],
        "related_topics": data.get("related_topics") or [],
        "confidence_score": float(data.get("confidence_score") or 0.0),
    }


async def generate_wiki_from_note(note_text: str, source_note_name: str) -> WikiPage:
    system = (
        "Return strict JSON with keys: title, summary, key_points (array), tags (array), "
        "related_topics (array), confidence_score (0..1)."
    )
    user = f"Create a concise wiki page from this note:\n\n{note_text[:12000]}"
    data = await ask_json(system, user)
    payload = _extract_json_or_fallback(data)
    payload["source_notes"] = [source_note_name]
    payload["created_at"] = _utc_now()
    payload["updated_at"] = _utc_now()
    payload["tags"] = normalize_tags([str(t) for t in payload.get("tags", [])])
    payload["related_topics"] = normalize_related_topics([str(t) for t in payload.get("related_topics", [])])
    return validate_and_fix_wiki_page(payload)


async def answer_query(question: str, context: str) -> dict[str, Any]:
    system = (
        "Answer from provided wiki context only. Return strict JSON with keys: "
        "answer (string), confidence_score (0..1)."
    )
    user = f"Question:\n{question}\n\nWiki context:\n{context[:18000]}"
    data = await ask_json(system, user)
    return {
        "answer": str(data.get("answer") or "No answer generated."),
        "confidence_score": float(data.get("confidence_score") or 0.0),
    }


def update_wiki_page(path_title: str, answer: str, tags: list[str]) -> WikiPage:
    path = wiki_path_for_title(path_title)
    page = load_wiki_page(path)
    page.summary = answer
    page.tags = normalize_tags(page.tags + tags)
    page.updated_at = _utc_now()
    save_wiki_page(page)
    return page


def create_new_page_from_query(title: str, answer: str, tags: list[str], confidence: float) -> WikiPage:
    page = WikiPage(
        title=title,
        summary=answer,
        key_points=[answer[:240]],
        tags=normalize_tags(tags),
        related_topics=[],
        source_notes=[],
        confidence_score=confidence,
    )
    save_wiki_page(page)
    return page

