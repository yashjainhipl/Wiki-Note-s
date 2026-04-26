from __future__ import annotations

from difflib import SequenceMatcher

from ..config import CONSOLIDATION_STRING_THRESHOLD, REFACTOR_REWRITE_MAX
from .file_handler import list_wiki_pages, load_wiki_page, save_wiki_page
from .tags import normalize_related_topics, normalize_tags


def run_refactor() -> dict:
    pages = [load_wiki_page(p) for p in list_wiki_pages()]
    merged_groups = 0
    pages_merged = 0
    pages_updated = 0
    pages_rewritten = 0
    errors: list[str] = []

    used = set()
    for i in range(len(pages)):
        if i in used:
            continue
        cluster = [i]
        for j in range(i + 1, len(pages)):
            if j in used:
                continue
            score = SequenceMatcher(a=pages[i].title.lower(), b=pages[j].title.lower()).ratio()
            if score >= CONSOLIDATION_STRING_THRESHOLD:
                cluster.append(j)
                used.add(j)
        if len(cluster) <= 1:
            continue
        merged_groups += 1
        canonical = pages[cluster[0]]
        for idx in cluster[1:]:
            dup = pages[idx]
            canonical.merged_from.append(dup.title)
            canonical.key_points = list(dict.fromkeys(canonical.key_points + dup.key_points))
            canonical.tags = normalize_tags(canonical.tags + dup.tags)
            canonical.related_topics = normalize_related_topics(canonical.related_topics + dup.related_topics)
            pages_merged += 1
        save_wiki_page(canonical)
        pages_updated += 1

    if REFACTOR_REWRITE_MAX > 0:
        for page in pages[:REFACTOR_REWRITE_MAX]:
            if len(page.summary) < 80 and page.key_points:
                page.summary = " ".join(page.key_points[:2])
                save_wiki_page(page)
                pages_rewritten += 1

    return {
        "merged_groups": merged_groups,
        "pages_merged": pages_merged,
        "pages_updated": pages_updated,
        "pages_rewritten": pages_rewritten,
        "errors": errors,
    }

