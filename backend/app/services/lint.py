from __future__ import annotations

from difflib import SequenceMatcher

from .file_handler import list_wiki_pages, load_wiki_page


def run_lint_checks() -> list[dict]:
    pages = [load_wiki_page(p) for p in list_wiki_pages()]
    issues: list[dict] = []

    for page in pages:
        if not page.summary.strip():
            issues.append({"rule": "empty_summary", "title": page.title})
        if len(page.tags) == 0:
            issues.append({"rule": "missing_tags", "title": page.title})
        if len(page.key_points) < 2:
            issues.append({"rule": "weak_key_points", "title": page.title})

    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            score = SequenceMatcher(a=pages[i].title.lower(), b=pages[j].title.lower()).ratio()
            if score >= 0.9:
                issues.append(
                    {
                        "rule": "duplicate_title_candidate",
                        "title": pages[i].title,
                        "other": pages[j].title,
                        "score": round(score, 3),
                    }
                )
    return issues

