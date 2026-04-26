from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import WIKI_PAGES_DIR
from ..services.file_handler import list_wiki_pages, load_wiki_page

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("")
def pages():
    output = []
    for path in list_wiki_pages():
        page = load_wiki_page(path)
        output.append(
            {
                "slug": path.stem,
                "path": path.name,
                "kind": (page.tags[0] if page.tags else "untagged"),
                "title": page.title,
            }
        )
    return output


@router.get("/{slug}")
def page(slug: str):
    matches = [p for p in list_wiki_pages() if p.stem == slug]
    if not matches:
        raise HTTPException(status_code=404, detail="Page not found.")
    path = matches[0]
    p = load_wiki_page(path)
    content = "\n".join(
        [
            f"# {p.title}",
            "",
            "## Summary",
            p.summary,
            "",
            "## Key Points",
            *[f"- {kp}" for kp in p.key_points],
            "",
            "## Tags",
            ", ".join(p.tags) if p.tags else "(none)",
            "",
            "## Related Topics",
            ", ".join(p.related_topics) if p.related_topics else "(none)",
        ]
    )
    return {
        "slug": slug,
        "path": path.name,
        "kind": (p.tags[0] if p.tags else "untagged"),
        "content": content,
    }

