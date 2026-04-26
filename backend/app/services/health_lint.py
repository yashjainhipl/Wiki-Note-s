from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from ..config import (
    HEALTH_LINT_BATCH_SIZE,
    HEALTH_LINT_MAX_ITEMS,
    HEALTH_LINT_MAX_PAGES,
    HEALTH_REPORTS_DIR,
    LLM_PROVIDER,
    OLLAMA_MODEL,
    OPENAI_MODEL,
)
from ..models.health_lint import HealthLintReport, MissingCrossRefItem, OrphanItem
from .file_handler import list_wiki_pages, load_wiki_page
from .llm import ask_json


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _active_model_name() -> str:
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    if LLM_PROVIDER == "ollama":
        return OLLAMA_MODEL
    return f"auto(ollama:{OLLAMA_MODEL}|openai:{OPENAI_MODEL})"


T = TypeVar("T")


def _chunks(items: list[T], size: int) -> list[list[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _truncate_unique(items: list[Any], max_items: int) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= max_items:
            break
    return out


def _compute_orphan_candidates(snapshot: list[dict[str, Any]]) -> list[dict[str, Any]]:
    titles = {p["title"] for p in snapshot}
    inbound = {title: 0 for title in titles}
    tag_buckets: dict[str, set[str]] = defaultdict(set)
    for page in snapshot:
        for rel in page.get("related_topics", []):
            if rel in inbound:
                inbound[rel] += 1
        for tag in page.get("tags", []):
            tag_buckets[str(tag).lower()].add(page["title"])
    tag_neighbors: dict[str, int] = {title: 0 for title in titles}
    for pages in tag_buckets.values():
        for title in pages:
            tag_neighbors[title] += max(0, len(pages) - 1)
    out: list[dict[str, Any]] = []
    for title in sorted(titles):
        in_count = inbound[title]
        neighbors = tag_neighbors[title]
        if in_count == 0 and neighbors <= 1:
            out.append(
                {
                    "page": title,
                    "reason": "No inbound related-topic links and weak tag connectivity.",
                    "inbound_count": in_count,
                    "tag_neighbors": neighbors,
                }
            )
    return out


def _compute_missing_cross_ref_candidates(snapshot: list[dict[str, Any]]) -> list[dict[str, Any]]:
    titles = {p["title"] for p in snapshot}
    existing: set[tuple[str, str]] = set()
    tags_to_pages: dict[str, set[str]] = defaultdict(set)
    for page in snapshot:
        source = page["title"]
        for rel in page.get("related_topics", []):
            if rel in titles and rel != source:
                existing.add((source, rel))
        for tag in page.get("tags", []):
            tags_to_pages[str(tag).lower()].add(source)

    candidates: list[dict[str, Any]] = []
    for tag, pages in tags_to_pages.items():
        pages_list = sorted(pages)
        if len(pages_list) < 2:
            continue
        for i, from_page in enumerate(pages_list):
            for to_page in pages_list[i + 1 :]:
                if (from_page, to_page) in existing or (to_page, from_page) in existing:
                    continue
                candidates.append(
                    {
                        "from_page": from_page,
                        "to_page": to_page,
                        "evidence": f"Shared tag '{tag}' without explicit related_topics links.",
                        "confidence": 0.55,
                    }
                )
    return candidates


def _snapshot_pages(max_pages: int) -> list[dict[str, Any]]:
    pages = [load_wiki_page(p) for p in list_wiki_pages()][:max_pages]
    return [
        {
            "title": p.title,
            "summary": p.summary,
            "key_points": p.key_points,
            "tags": p.tags,
            "related_topics": p.related_topics,
            "source_notes": p.source_notes,
            "updated_at": p.updated_at,
        }
        for p in pages
    ]


def _json_schema_instruction() -> str:
    return (
        "Return strict JSON object with keys: contradictions, stale_claims, orphans, "
        "missing_pages, missing_cross_refs, data_gaps_web_search, next_actions. "
        "Each key must be an array. Keep items concise and evidence-based. "
        "Item schemas: contradictions[{page_a,page_b,claim_a,claim_b,confidence,rationale}], "
        "stale_claims[{page,claim,superseded_by_source,suggested_update,confidence}], "
        "orphans[{page,reason,inbound_count,tag_neighbors}], "
        "missing_pages[{concept,mentioned_in_pages,why_needed,confidence}], "
        "missing_cross_refs[{from_page,to_page,evidence,confidence}], "
        "data_gaps_web_search[{question_to_investigate,suggested_queries,candidate_sources}], "
        "next_actions[{action,severity,effort,rationale}]."
    )


def _batch_prompt(batch: list[dict[str, Any]], deterministic: dict[str, Any]) -> str:
    return (
        "Analyze this wiki batch for health issues.\n"
        "Focus on: contradictions, stale claims, orphan pages, missing concept pages, missing cross-references, and data gaps.\n"
        "Use deterministic hints as priors, but verify against content.\n\n"
        f"Deterministic hints:\n{json.dumps(deterministic, ensure_ascii=False)}\n\n"
        f"Wiki pages:\n{json.dumps(batch, ensure_ascii=False)}"
    )


async def _lint_batch(batch: list[dict[str, Any]], deterministic: dict[str, Any]) -> dict[str, Any]:
    system = _json_schema_instruction()
    user = _batch_prompt(batch, deterministic)
    return await ask_json(system, user)


def _merge_arrays(payloads: list[dict[str, Any]]) -> dict[str, list[Any]]:
    keys = [
        "contradictions",
        "stale_claims",
        "orphans",
        "missing_pages",
        "missing_cross_refs",
        "data_gaps_web_search",
        "next_actions",
    ]
    out: dict[str, list[Any]] = {k: [] for k in keys}
    for payload in payloads:
        for key in keys:
            values = payload.get(key, [])
            if isinstance(values, list):
                out[key].extend(values)
    return out


def _to_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_lint_shape(merged: dict[str, list[Any]]) -> tuple[dict[str, list[Any]], list[str]]:
    notes: list[str] = []
    out = dict(merged)

    contradictions: list[dict[str, Any]] = []
    for item in out.get("contradictions", []):
        if not isinstance(item, dict):
            continue
        pages = _to_list(item.get("pages"))
        page_a = str(item.get("page_a") or (pages[0] if len(pages) >= 1 else "")).strip()
        page_b = str(item.get("page_b") or (pages[1] if len(pages) >= 2 else "")).strip()
        claim_a = str(item.get("claim_a") or item.get("statement_a") or item.get("claim") or "").strip()
        claim_b = str(item.get("claim_b") or item.get("statement_b") or item.get("counter_claim") or "").strip()
        if page_a and page_b:
            contradictions.append(
                {
                    "page_a": page_a,
                    "page_b": page_b,
                    "claim_a": claim_a or "Potential contradiction identified.",
                    "claim_b": claim_b or str(item.get("rationale") or "Conflicting claim detected."),
                    "confidence": _to_float(item.get("confidence"), 0.5),
                    "rationale": str(item.get("rationale") or "").strip(),
                }
            )
    out["contradictions"] = contradictions

    missing_pages: list[dict[str, Any]] = []
    for item in out.get("missing_pages", []):
        if not isinstance(item, dict):
            continue
        concept = str(item.get("concept") or item.get("missing_concept") or "").strip()
        if concept:
            missing_pages.append(
                {
                    "concept": concept,
                    "mentioned_in_pages": _to_list(item.get("mentioned_in_pages") or item.get("pages")),
                    "why_needed": str(item.get("why_needed") or item.get("reason") or "").strip(),
                    "confidence": _to_float(item.get("confidence"), 0.5),
                }
            )
    out["missing_pages"] = missing_pages

    gaps: list[dict[str, Any]] = []
    for item in out.get("data_gaps_web_search", []):
        if not isinstance(item, dict):
            continue
        question = str(item.get("question_to_investigate") or "").strip()
        if not question:
            page = str(item.get("page") or "").strip()
            gap = str(item.get("gap") or "").strip()
            question = f"{page}: {gap}".strip(": ").strip()
        if question:
            gaps.append(
                {
                    "question_to_investigate": question,
                    "suggested_queries": _to_list(item.get("suggested_queries") or item.get("queries")),
                    "candidate_sources": _to_list(item.get("candidate_sources") or item.get("sources")),
                }
            )
    out["data_gaps_web_search"] = gaps

    actions: list[dict[str, Any]] = []
    for item in out.get("next_actions", []):
        if isinstance(item, str):
            action = item.strip()
            if action:
                actions.append({"action": action, "severity": "medium", "effort": "medium", "rationale": ""})
        elif isinstance(item, dict):
            action = str(item.get("action") or item.get("task") or item.get("title") or "").strip()
            if action:
                actions.append(
                    {
                        "action": action,
                        "severity": str(item.get("severity") or "medium"),
                        "effort": str(item.get("effort") or "medium"),
                        "rationale": str(item.get("rationale") or item.get("why") or "").strip(),
                    }
                )
    out["next_actions"] = actions

    if out != merged:
        notes.append("schema_normalization_applied")
    return out, notes


def _report_path() -> Path:
    return HEALTH_REPORTS_DIR / f"{_utc_stamp()}-health-lint.json"


def _serialize_report(report: HealthLintReport) -> dict[str, Any]:
    if hasattr(report, "model_dump"):
        return report.model_dump()
    return report.dict()


def _serialize_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _validate_report(data: dict[str, Any]) -> HealthLintReport:
    if hasattr(HealthLintReport, "model_validate"):
        return HealthLintReport.model_validate(data)
    return HealthLintReport(**data)


async def run_health_lint() -> dict[str, Any]:
    snapshot = _snapshot_pages(HEALTH_LINT_MAX_PAGES)
    deterministic_orphans = _compute_orphan_candidates(snapshot)
    deterministic_cross_refs = _compute_missing_cross_ref_candidates(snapshot)
    deterministic_hints = {
        "orphans": deterministic_orphans[:HEALTH_LINT_MAX_ITEMS],
        "missing_cross_refs": deterministic_cross_refs[:HEALTH_LINT_MAX_ITEMS],
    }

    payloads: list[dict[str, Any]] = []
    errors: list[str] = []
    for batch in _chunks(snapshot, HEALTH_LINT_BATCH_SIZE):
        try:
            payloads.append(await _lint_batch(batch, deterministic_hints))
        except Exception as exc:  # pragma: no cover - network/provider failures
            errors.append(f"batch_failure: {exc}")

    merged = _merge_arrays(payloads)
    merged, normalization_notes = _normalize_lint_shape(merged)
    merged["orphans"].extend(deterministic_orphans)
    merged["missing_cross_refs"].extend(deterministic_cross_refs)
    for key in list(merged.keys()):
        merged[key] = _truncate_unique(merged[key], HEALTH_LINT_MAX_ITEMS)

    report_data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pages_analyzed": len(snapshot),
        "model": _active_model_name(),
        "version": "1",
        "contradictions": merged["contradictions"],
        "stale_claims": merged["stale_claims"],
        "orphans": [_serialize_model(OrphanItem(**x)) for x in merged["orphans"]],
        "missing_pages": merged["missing_pages"],
        "missing_cross_refs": [_serialize_model(MissingCrossRefItem(**x)) for x in merged["missing_cross_refs"]],
        "data_gaps_web_search": merged["data_gaps_web_search"],
        "next_actions": merged["next_actions"],
        "errors": [*errors, *normalization_notes],
    }
    report = _validate_report(report_data)
    path = _report_path()
    path.write_text(json.dumps(_serialize_report(report), ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {
        "contradictions": len(report.contradictions),
        "stale_claims": len(report.stale_claims),
        "orphans": len(report.orphans),
        "missing_pages": len(report.missing_pages),
        "missing_cross_refs": len(report.missing_cross_refs),
        "data_gaps_web_search": len(report.data_gaps_web_search),
    }
    return {
        "report_path": str(path),
        "report": _serialize_report(report),
        "counts": counts,
        "next_actions": _serialize_report(report).get("next_actions", [])[:8],
    }


def get_latest_health_lint_report() -> dict[str, Any]:
    files = sorted(HEALTH_REPORTS_DIR.glob("*.json"))
    if not files:
        return {"report": None, "counts": {}, "report_path": None}
    latest = files[-1]
    report = _validate_report(json.loads(latest.read_text(encoding="utf-8")))
    out = _serialize_report(report)
    return {
        "report_path": str(latest),
        "report": out,
        "counts": {
            "contradictions": len(report.contradictions),
            "stale_claims": len(report.stale_claims),
            "orphans": len(report.orphans),
            "missing_pages": len(report.missing_pages),
            "missing_cross_refs": len(report.missing_cross_refs),
            "data_gaps_web_search": len(report.data_gaps_web_search),
        },
    }

