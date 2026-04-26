from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..config import RAW_NOTES_DIR
from ..services.file_handler import save_raw_note
from ..services.parser import parse_file

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestTextRequest(BaseModel):
    text: str
    filename_hint: str = "raw-text.txt"


def _store_upload_temporarily(upload: UploadFile) -> Path:
    tmp = RAW_NOTES_DIR / f"tmp-{upload.filename or 'upload.bin'}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return tmp


@router.post("/upload")
async def ingest_upload(file: UploadFile = File(...)):
    temp = _store_upload_temporarily(file)
    try:
        text = parse_file(temp)
    finally:
        if temp.exists():
            temp.unlink()
    note_path = save_raw_note(file.filename or "upload.txt", text)
    return {"status": "ok", "raw_note": note_path.name}


@router.post("/upload/batch")
async def ingest_batch(files: list[UploadFile] = File(...)):
    successes = []
    errors = []
    for file in files:
        try:
            temp = _store_upload_temporarily(file)
            try:
                text = parse_file(temp)
            finally:
                if temp.exists():
                    temp.unlink()
            note_path = save_raw_note(file.filename or "upload.txt", text)
            successes.append({"file": file.filename, "raw_note": note_path.name})
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": file.filename, "error": str(exc)})
    return {"successes": successes, "errors": errors}


@router.post("")
async def ingest_text(payload: IngestTextRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    note_path = save_raw_note(payload.filename_hint, payload.text)
    return {"status": "ok", "raw_note": note_path.name}

