from __future__ import annotations

from fastapi import APIRouter

from ..services.graph import build_graph_payload

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
def graph():
    return build_graph_payload()

