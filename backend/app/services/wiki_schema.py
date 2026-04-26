from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..models import WikiPage
from .tags import normalize_related_topics, normalize_tags


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_and_fix_wiki_page(payload: dict[str, Any]) -> WikiPage:
    base = {
        "title": str(payload.get("title") or "Untitled"),
        "summary": str(payload.get("summary") or ""),
        "key_points": [str(x) for x in payload.get("key_points") or []],
        "tags": normalize_tags([str(x) for x in payload.get("tags") or []]),
        "related_topics": normalize_related_topics([str(x) for x in payload.get("related_topics") or []]),
        "source_notes": [str(x) for x in payload.get("source_notes") or []],
        "merged_from": [str(x) for x in payload.get("merged_from") or []],
        "created_at": str(payload.get("created_at") or _utc_now()),
        "updated_at": str(payload.get("updated_at") or _utc_now()),
        "confidence_score": float(payload.get("confidence_score") or 0.0),
    }
    return WikiPage(**base)

