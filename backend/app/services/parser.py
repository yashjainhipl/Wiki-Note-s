from __future__ import annotations

from pathlib import Path

from docx import Document
from pypdf import PdfReader


def normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def parse_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return normalize_text("\n".join(page.extract_text() or "" for page in reader.pages))
    if suffix == ".docx":
        doc = Document(str(path))
        return normalize_text("\n".join(p.text for p in doc.paragraphs))
    raise ValueError(f"Unsupported file type: {suffix}")

