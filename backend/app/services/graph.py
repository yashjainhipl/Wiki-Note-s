from __future__ import annotations

from collections import defaultdict

from .file_handler import list_wiki_pages, load_wiki_page


def build_graph_payload() -> dict:
    pages = [load_wiki_page(p) for p in list_wiki_pages()]
    title_to_node = {p.title: p for p in pages}
    nodes = []
    links = []

    for page in pages:
        nodes.append(
            {
                "id": page.title,
                "title": page.title,
                "summary": page.summary,
                "tags": page.tags,
                "key_points": page.key_points,
                "source_notes": page.source_notes,
                "group": (page.tags[0] if page.tags else "untagged"),
            }
        )

    seen: set[tuple[str, str, str]] = set()
    for page in pages:
        for rel in page.related_topics:
            if rel in title_to_node:
                key = (page.title, rel, "related")
                if key not in seen:
                    seen.add(key)
                    links.append({"source": page.title, "target": rel, "type": "related"})

    tag_buckets: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        for tag in page.tags:
            tag_buckets[tag].append(page.title)
    for titles in tag_buckets.values():
        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                key = (titles[i], titles[j], "shared_tag")
                if key not in seen:
                    seen.add(key)
                    links.append({"source": titles[i], "target": titles[j], "type": "shared_tag"})

    return {"nodes": nodes, "links": links}

