from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class WikiPage(BaseModel):
    title: str
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    merged_from: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    confidence_score: float = 0.0

