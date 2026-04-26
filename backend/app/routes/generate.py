from __future__ import annotations

import asyncio

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import GENERATE_CONCURRENCY
from ..services.file_handler import list_raw_notes, read_raw_note, save_wiki_page
from ..services.wiki import generate_wiki_from_note

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateFromRawRequest(BaseModel):
    raw_note_filenames: list[str]


async def _generate_for_note(path_name: str):
    from ..config import RAW_NOTES_DIR

    path = RAW_NOTES_DIR / path_name
    text = read_raw_note(path)
    page = await generate_wiki_from_note(text, source_note_name=path.name)
    out = save_wiki_page(page)
    return {"raw_note": path.name, "wiki_file": out.name, "title": page.title}


async def _run_generation(paths: list[str]):
    sem = asyncio.Semaphore(GENERATE_CONCURRENCY)

    async def run_one(name: str):
        async with sem:
            return await _generate_for_note(name)

    return await asyncio.gather(*(run_one(name) for name in paths), return_exceptions=True)


@router.post("")
async def generate_all():
    names = [p.name for p in list_raw_notes()]
    results = await _run_generation(names)
    ok, errors = [], []
    for r in results:
        if isinstance(r, Exception):
            errors.append(str(r))
        else:
            ok.append(r)
    return {"generated": ok, "errors": errors}


@router.post("/from-raw")
async def generate_from_raw(payload: GenerateFromRawRequest):
    results = await _run_generation(payload.raw_note_filenames)
    ok, errors = [], []
    for r in results:
        if isinstance(r, Exception):
            errors.append(str(r))
        else:
            ok.append(r)
    return {"generated": ok, "errors": errors}

