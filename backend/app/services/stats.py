from __future__ import annotations

from collections import Counter
from datetime import datetime

from .file_handler import list_wiki_pages, load_wiki_page
from .graph import build_graph_payload


def compute_stats() -> dict:
    page_paths = list_wiki_pages()
    pages = [(p, load_wiki_page(p)) for p in page_paths]
    graph = build_graph_payload()
    tags = Counter(tag for _, p in pages for tag in p.tags)
    recent = sorted(
        (
            {
                "filename": path.name,
                "title": p.title,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "tags": p.tags,
            }
            for path, p in pages
        ),
        key=lambda x: datetime.fromisoformat(x["updated_at"].replace("Z", "+00:00")),
        reverse=True,
    )[:10]
    return {
        "total_nodes": len(graph["nodes"]),
        "total_edges": len(graph["links"]),
        "recent_nodes": recent,
        "top_tags": [{"tag": tag, "count": count} for tag, count in tags.most_common(20)],
    }

