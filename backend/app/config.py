import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
LLM_FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "1").lower() not in {"0", "false", "no"}
LLM_STRICT_PRIMARY = os.getenv("LLM_STRICT_PRIMARY", "0").lower() in {"1", "true", "yes"}
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION", "")
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT", "")
WIKI_WRITEBACK_CONFIDENCE_THRESHOLD = float(os.getenv("WIKI_WRITEBACK_CONFIDENCE_THRESHOLD", "0.6"))
GENERATE_CONCURRENCY = max(1, min(16, int(os.getenv("GENERATE_CONCURRENCY", "4"))))
CONSOLIDATION_STRING_THRESHOLD = float(os.getenv("CONSOLIDATION_STRING_THRESHOLD", "0.82"))
WIKI_VERSION_SNAPSHOTS = os.getenv("WIKI_VERSION_SNAPSHOTS", "1").lower() not in {"0", "false", "no"}
REFACTOR_REWRITE_MAX = int(os.getenv("REFACTOR_REWRITE_MAX", "0"))
QUERY_CONTEXT_PAGE_LIMIT = int(os.getenv("QUERY_CONTEXT_PAGE_LIMIT", "5"))
QUERY_CONTEXT_CHARS_PER_PAGE = int(os.getenv("QUERY_CONTEXT_CHARS_PER_PAGE", "2500"))
HEALTH_LINT_BATCH_SIZE = max(5, min(80, int(os.getenv("HEALTH_LINT_BATCH_SIZE", "30"))))
HEALTH_LINT_MAX_PAGES = max(10, min(5000, int(os.getenv("HEALTH_LINT_MAX_PAGES", "500"))))
HEALTH_LINT_MAX_ITEMS = max(3, min(200, int(os.getenv("HEALTH_LINT_MAX_ITEMS", "40"))))
RAW_NOTES_DIR = BACKEND_DIR / "raw_notes"
WIKI_PAGES_DIR = BACKEND_DIR / "wiki_pages"
WIKI_VERSIONS_DIR = WIKI_PAGES_DIR / "_versions"
HEALTH_REPORTS_DIR = WIKI_PAGES_DIR / "health_reports"

for _path in [
    RAW_NOTES_DIR,
    WIKI_PAGES_DIR,
    WIKI_VERSIONS_DIR,
    HEALTH_REPORTS_DIR,
]:
    _path.mkdir(parents=True, exist_ok=True)
