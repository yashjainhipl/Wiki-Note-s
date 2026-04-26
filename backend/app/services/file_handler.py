from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..config import RAW_NOTES_DIR, WIKI_PAGES_DIR, WIKI_VERSIONS_DIR, WIKI_VERSION_SNAPSHOTS
from ..models import WikiPage

INDEX_FILE = "index.md"
LOG_FILE = "log.md"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def safe_stem(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem or "note"


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


def save_raw_note(filename_hint: str, text: str) -> Path:
    safe = safe_stem(filename_hint)
    out = RAW_NOTES_DIR / f"{_utc_stamp()}-{safe}-{uuid4().hex[:8]}.txt"
    out.write_text(text, encoding="utf-8")
    return out


def list_raw_notes() -> list[Path]:
    return sorted(RAW_NOTES_DIR.glob("*.txt"))


def read_raw_note(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def wiki_path_for_title(title: str) -> Path:
    return WIKI_PAGES_DIR / f"{slugify_title(title)}.md"


def is_meta_page(path: Path) -> bool:
    if not path.is_file():
        return True
    return path.name in {INDEX_FILE, LOG_FILE}


def ensure_meta_files() -> None:
    index_path = WIKI_PAGES_DIR / INDEX_FILE
    log_path = WIKI_PAGES_DIR / LOG_FILE
    if not index_path.exists():
        index_path.write_text("# Index\n", encoding="utf-8")
    if not log_path.exists():
        log_path.write_text("# Log\n", encoding="utf-8")


def _markdown_for_page(page: WikiPage) -> str:
    return "\n".join(
        [
            f"# {page.title}",
            "",
            "## Summary",
            page.summary.strip(),
            "",
            "## Key Points",
            *[f"- {x}" for x in page.key_points],
            "",
            "## Tags",
            *[f"- {x}" for x in page.tags],
            "",
            "## Related Topics",
            *[f"- {x}" for x in page.related_topics],
            "",
            "## Source Notes",
            *[f"- {x}" for x in page.source_notes],
            "",
            "## Merged From",
            *[f"- {x}" for x in page.merged_from],
            "",
            "## Metadata",
            f"- created_at: {page.created_at}",
            f"- updated_at: {page.updated_at}",
            f"- confidence_score: {page.confidence_score}",
            "",
        ]
    )


def _parse_markdown_page(text: str) -> WikiPage:
    lines = text.splitlines()
    title = "Untitled"
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip() or "Untitled"

    sections: dict[str, list[str]] = {}
    current = ""
    for line in lines[1:]:
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    def bullets(section: str) -> list[str]:
        out = []
        for row in sections.get(section, []):
            s = row.strip()
            if s.startswith("- "):
                out.append(s[2:].strip())
        return [x for x in out if x]

    summary_lines = [row for row in sections.get("summary", []) if row.strip()]
    summary = "\n".join(summary_lines).strip()

    metadata = {}
    for item in bullets("metadata"):
        if ":" in item:
            k, v = item.split(":", 1)
            metadata[k.strip()] = v.strip()

    return WikiPage(
        title=title,
        summary=summary,
        key_points=bullets("key points"),
        tags=bullets("tags"),
        related_topics=bullets("related topics"),
        source_notes=bullets("source notes"),
        merged_from=bullets("merged from"),
        created_at=metadata.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        updated_at=metadata.get("updated_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        confidence_score=float(metadata.get("confidence_score", "0.0") or 0.0),
    )


def save_wiki_page(page: WikiPage) -> Path:
    ensure_meta_files()
    path = wiki_path_for_title(page.title)
    if path.exists() and WIKI_VERSION_SNAPSHOTS:
        version = WIKI_VERSIONS_DIR / f"{path.stem}-{_utc_stamp()}-{uuid4().hex[:6]}.md"
        version.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(_markdown_for_page(page), encoding="utf-8")
    rebuild_index_md()
    return path


def load_wiki_page(path: Path) -> WikiPage:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return WikiPage(**json.loads(text))
    return _parse_markdown_page(text)


def list_wiki_pages() -> list[Path]:
    ensure_meta_files()
    pages = [p for p in WIKI_PAGES_DIR.glob("*.md") if p.is_file()]
    # Backward-compatible read support for older JSON pages.
    pages.extend(p for p in WIKI_PAGES_DIR.glob("*.json") if p.is_file())
    return sorted(p for p in pages if not is_meta_page(p))


def rebuild_index_md() -> None:
    ensure_meta_files()
    index_path = WIKI_PAGES_DIR / INDEX_FILE
    entries: list[str] = ["# Index", ""]
    pages = list_wiki_pages()
    pages.sort(key=lambda p: p.stem.lower())
    for path in pages:
        page = load_wiki_page(path)
        tags = ", ".join(page.tags) if page.tags else "none"
        entries.append(
            f"- [{path.stem}]({path.name}) | title: {page.title} | tags: {tags} | updated: {page.updated_at}"
        )
    if len(entries) == 2:
        entries.append("- (no knowledge pages yet)")
    entries.append("")
    index_path.write_text("\n".join(entries), encoding="utf-8")


def append_query_log(
    *,
    question: str,
    action: str,
    confidence: float,
    updated_node: str | None,
    wiki_file: str | None,
) -> None:
    ensure_meta_files()
    path = WIKI_PAGES_DIR / LOG_FILE
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    short_q = " ".join(question.split())
    if len(short_q) > 140:
        short_q = short_q[:137] + "..."
    block = [
        f"## [{now}] query | {short_q}",
        f"- action: {action}",
        f"- confidence: {confidence:.3f}",
        f"- updated_node: {updated_node or 'none'}",
        f"- wiki_file: {wiki_file or 'none'}",
        "",
    ]
    existing = path.read_text(encoding="utf-8")
    if not existing.startswith("# Log"):
        existing = "# Log\n"
    body = existing.split("\n", 1)[1] if "\n" in existing else ""
    path.write_text("# Log\n\n" + "\n".join(block) + body.lstrip("\n"), encoding="utf-8")

