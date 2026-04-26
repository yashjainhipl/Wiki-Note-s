from __future__ import annotations

from .file_handler import list_wiki_pages, load_wiki_page


def rank_pages(question: str, limit: int = 5) -> list[tuple[int, str]]:
    terms = {t.lower() for t in question.split() if len(t) > 3}
    ranked: list[tuple[int, str]] = []
    for path in list_wiki_pages():
        page = load_wiki_page(path)
        blob = " ".join(
            [
                page.title,
                page.summary,
                " ".join(page.key_points),
                " ".join(page.tags),
                " ".join(page.related_topics),
            ]
        ).lower()
        score = sum(1 for term in terms if term in blob)
        if score > 0:
            ranked.append((score, path.name))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[:limit]

