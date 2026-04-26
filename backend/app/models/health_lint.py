from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ContradictionItem(BaseModel):
    page_a: str
    page_b: str
    claim_a: str
    claim_b: str
    confidence: float = 0.0
    rationale: str = ""


class StaleClaimItem(BaseModel):
    page: str
    claim: str
    superseded_by_source: str = ""
    suggested_update: str = ""
    confidence: float = 0.0


class OrphanItem(BaseModel):
    page: str
    reason: str = ""
    inbound_count: int = 0
    tag_neighbors: int = 0


class MissingPageItem(BaseModel):
    concept: str
    mentioned_in_pages: list[str] = Field(default_factory=list)
    why_needed: str = ""
    confidence: float = 0.0


class MissingCrossRefItem(BaseModel):
    from_page: str
    to_page: str
    evidence: str = ""
    confidence: float = 0.0


class DataGapItem(BaseModel):
    question_to_investigate: str
    suggested_queries: list[str] = Field(default_factory=list)
    candidate_sources: list[str] = Field(default_factory=list)


class NextActionItem(BaseModel):
    action: str
    severity: str = "medium"
    effort: str = "medium"
    rationale: str = ""


class HealthLintReport(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    pages_analyzed: int = 0
    model: str = ""
    version: str = "1"
    contradictions: list[ContradictionItem] = Field(default_factory=list)
    stale_claims: list[StaleClaimItem] = Field(default_factory=list)
    orphans: list[OrphanItem] = Field(default_factory=list)
    missing_pages: list[MissingPageItem] = Field(default_factory=list)
    missing_cross_refs: list[MissingCrossRefItem] = Field(default_factory=list)
    data_gaps_web_search: list[DataGapItem] = Field(default_factory=list)
    next_actions: list[NextActionItem] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

