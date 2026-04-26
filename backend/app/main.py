from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env before importing modules that read config at import time.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .routes import (
    generate_router,
    graph_router,
    ingest_router,
    lint_router,
    pages_router,
    query_router,
    refactor_router,
    stats_router,
)
from .services.llm import close_async_openai_client

app = FastAPI(title="Knowledge Engine API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(generate_router)
app.include_router(query_router)
app.include_router(graph_router)
app.include_router(pages_router)
app.include_router(stats_router)
app.include_router(refactor_router)
app.include_router(lint_router)


@app.on_event("startup")
async def startup() -> None:
    return None


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_async_openai_client()


@app.get("/health")
def health() -> dict:
    return {"ok": True}
