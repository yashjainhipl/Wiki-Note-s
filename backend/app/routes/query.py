from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import WIKI_WRITEBACK_CONFIDENCE_THRESHOLD
from ..services.file_handler import append_query_log, load_wiki_page, wiki_path_for_title
from ..services.search import rank_pages
from ..services.wiki import answer_query, create_new_page_from_query, update_wiki_page

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str


@router.post("")
async def query(payload: QueryRequest):
    ranked = rank_pages(payload.question, limit=5)
    used_files = [name for _, name in ranked]
    used_pages = []
    context_chunks = []
    from ..config import WIKI_PAGES_DIR

    for file_name in used_files:
        page = load_wiki_page(WIKI_PAGES_DIR / file_name)
        used_pages.append(page.title)
        context_chunks.append(
            f"Title: {page.title}\nSummary: {page.summary}\nKey points: {'; '.join(page.key_points)}\nTags: {', '.join(page.tags)}"
        )
    result = await answer_query(payload.question, "\n\n".join(context_chunks))
    answer = result["answer"]
    confidence = float(result["confidence_score"])

    wiki_action = "none"
    wiki_file = None
    updated_node = None
    if confidence > WIKI_WRITEBACK_CONFIDENCE_THRESHOLD:
        if used_pages:
            updated = update_wiki_page(used_pages[0], answer, tags=payload.question.split()[:3])
            wiki_action = "updated"
            wiki_file = wiki_path_for_title(updated.title).name
            updated_node = updated.title
        else:
            title = payload.question.strip().rstrip("?")[:80] or "New knowledge"
            created = create_new_page_from_query(title, answer, payload.question.split()[:3], confidence)
            wiki_action = "created"
            wiki_file = wiki_path_for_title(created.title).name
            updated_node = created.title

    append_query_log(
        question=payload.question,
        action=wiki_action,
        confidence=confidence,
        updated_node=updated_node,
        wiki_file=wiki_file,
    )

    return {
        "answer": answer,
        "used_nodes": used_pages,
        "updated_node": updated_node,
        "confidence_score": confidence,
        "wiki_action": wiki_action,
        "wiki_file": wiki_file,
    }

