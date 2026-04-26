from __future__ import annotations

from fastapi import APIRouter, Query

from ..services.health_lint import get_latest_health_lint_report, run_health_lint
from ..services.lint import run_lint_checks

router = APIRouter(prefix="/lint", tags=["lint"])


@router.get("")
def lint(suggest: bool = Query(default=False)):
    issues = run_lint_checks()
    out = {"issues": issues}
    if suggest:
        out["suggestions"] = [
            "Add tags to pages flagged with missing_tags.",
            "Expand summary/key points for weak pages.",
            "Merge high-similarity duplicate title candidates.",
        ]
    return out


@router.post("/health")
async def lint_health():
    return await run_health_lint()


@router.get("/health/latest")
def lint_health_latest():
    return get_latest_health_lint_report()

