from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
import os
import tempfile
import shutil
from typing import List, Dict, Any
from datetime import datetime, timedelta

from .dictionary import (
    load_cmu_dict,
    ipa_to_phonemes,
    build_reverse_cmu_dict,
)
from .encoder import encode_text_to_music
from .decoder import decode_midi_file

limiter = Limiter(key_func=get_remote_address)
scheduler = BackgroundScheduler()

app = FastAPI(
    title="Text to Music API",
    description="Encode text to music via IPA phonemes and decode music back to text",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

MAX_TEXT_LENGTH = 500
MAX_FILE_SIZE = 5 * 1024 * 1024
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
CLEANUP_AGE_DAYS = 7
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/favicon.svg")
async def favicon():
    favicon_path = os.path.join(FRONTEND_DIR, "favicon.svg")
    return FileResponse(favicon_path, media_type="image/svg+xml")


cmu_dict = None
reverse_cmu_dict = None


def cleanup_old_outputs():
    if not os.path.exists(OUTPUTS_DIR):
        return

    cutoff_time = datetime.now() - timedelta(days=CLEANUP_AGE_DAYS)
    cleaned = 0

    for folder in os.listdir(OUTPUTS_DIR):
        folder_path = os.path.join(OUTPUTS_DIR, folder)
        if os.path.isdir(folder_path):
            folder_mtime = datetime.fromtimestamp(os.path.getmtime(folder_path))
            if folder_mtime < cutoff_time:
                try:
                    shutil.rmtree(folder_path)
                    cleaned += 1
                except Exception as e:
                    print(f"Failed to delete {folder_path}: {e}")

    if cleaned > 0:
        print(f"Cleaned up {cleaned} old output folder(s)")


@app.on_event("startup")
async def startup_event():
    global cmu_dict, reverse_cmu_dict
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "en_US.txt")
    cmu_dict = load_cmu_dict(data_path)
    reverse_cmu_dict = build_reverse_cmu_dict(cmu_dict)
    print(f"Loaded {len(cmu_dict)} words from dictionary")
    print(f"Built reverse dictionary with {len(reverse_cmu_dict)} entries")
    cleanup_old_outputs()

    scheduler.add_job(cleanup_old_outputs, "cron", hour=3, minute=0)
    scheduler.start()
    print("Scheduled daily cleanup at 3:00 AM")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down")


class EncodeRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long (max {MAX_TEXT_LENGTH} characters)")
        return v.strip()


class EncodeResponse(BaseModel):
    success: bool
    ipa: str
    note_count: int
    midi_file: str
    notes: List[Dict[str, Any]]
    phonemes: List[str]
    message: str


class DecodeResponse(BaseModel):
    success: bool
    decoded_text: str
    message: str


@app.get("/", response_class=HTMLResponse)
@limiter.limit("100/minute")
async def root(request: Request):
    html_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/encode", response_model=EncodeResponse)
@limiter.limit("10/minute")
async def encode_text(request: Request, encode_request: EncodeRequest):
    if not cmu_dict:
        raise HTTPException(status_code=500, detail="Dictionary not loaded")

    try:
        ipa, notes, midi_path = encode_text_to_music(encode_request.text, cmu_dict)
        phonemes = ipa_to_phonemes(ipa)
        note_data = []
        current_time = 0.0

        for i, (pitch, duration, velocity) in enumerate(notes):
            phoneme = phonemes[i] if i < len(phonemes) else ""
            phoneme_clean = phoneme.replace("ˈ", "").replace("ˌ", "")

            note_data.append(
                {
                    "pitch": pitch,
                    "duration": duration,
                    "velocity": velocity,
                    "time": current_time,
                    "phoneme": phoneme_clean,
                }
            )
            current_time += duration

        return EncodeResponse(
            success=True,
            ipa=ipa,
            note_count=len(notes),
            midi_file=midi_path,
            notes=note_data,
            phonemes=[p.replace("ˈ", "").replace("ˌ", "") for p in phonemes],
            message=f"Successfully encoded text to {midi_path}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encoding failed: {str(e)}")


@app.post("/decode", response_model=DecodeResponse)
@limiter.limit("10/minute")
async def decode_music(request: Request, file: UploadFile = File(...)):
    if not reverse_cmu_dict:
        raise HTTPException(status_code=500, detail="Dictionary not loaded")

    if not file.filename.endswith(".mid") and not file.filename.endswith(".midi"):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Must be .mid or .midi"
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)",
        )

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp:
            temp_file = temp.name
            shutil.copyfileobj(file.file, temp)

        decoded_text = decode_midi_file(temp_file, reverse_cmu_dict)

        return DecodeResponse(
            success=True,
            decoded_text=decoded_text,
            message="Successfully decoded MIDI file",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decoding failed: {str(e)}")

    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


@app.get("/download/{path:path}")
@limiter.limit("30/minute")
async def download_file(request: Request, path: str):
    if not path.startswith("outputs/"):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        media_type="audio/midi",
        filename=os.path.basename(path),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
