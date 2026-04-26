from __future__ import annotations

from fastapi import APIRouter

from ..services.stats import compute_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def stats():
    return compute_stats()

