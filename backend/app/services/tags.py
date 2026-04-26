from __future__ import annotations


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for tag in tags:
        t = tag.strip().lower()
        if not t:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:20]


def normalize_related_topics(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        val = item.strip()
        if not val:
            continue
        key = val.lower()
        if key not in seen:
            seen.add(key)
            out.append(val)
    return out[:40]

