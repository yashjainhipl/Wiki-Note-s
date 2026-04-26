from __future__ import annotations

from fastapi import APIRouter

from ..services.refactor import run_refactor

router = APIRouter(prefix="/refactor", tags=["refactor"])


@router.post("")
def refactor():
    return run_refactor()

