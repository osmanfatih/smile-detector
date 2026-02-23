"""
Smile Detector — FastAPI backend
Serves the frontend and handles:
  - WebSocket /ws  : real-time smile detection frames
  - POST /submit-email : save name + email
  - GET  /emails   : list all submissions (admin)
"""

import base64
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import create_tables, get_all_submissions, save_submission
from detector import SmileDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating DB tables...")
    await create_tables()
    logger.info("Smile Detector ready 🎉  →  http://localhost:8000")
    yield


app = FastAPI(title="Smile Detector", lifespan=lifespan)

# Serve static assets (CSS, JS if split out)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Single shared detector instance (MediaPipe is not thread-safe but we're async)
detector = SmileDetector()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    html_file = FRONTEND_DIR / "index.html"
    return FileResponse(str(html_file), media_type="text/html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            # Receive base64-encoded JPEG frame
            data = await websocket.receive_text()

            # Strip data-URL prefix if present
            if data.startswith("data:"):
                # e.g. "data:image/jpeg;base64,/9j/..."
                data = data.split(",", 1)[1]

            try:
                frame_bytes = base64.b64decode(data)
                result = detector.detect(frame_bytes)
            except Exception as e:
                logger.warning(f"Detection error: {e}")
                result = {"status": "NO_FACE", "smile_score": 0.0, "message": "Processing error"}

            await websocket.send_json(result)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")


class SubmitRequest(BaseModel):
    name: str
    email: str


@app.post("/submit-email")
async def submit_email(req: SubmitRequest):
    if not req.name.strip() or not req.email.strip():
        return JSONResponse({"success": False, "error": "Name and email are required"}, status_code=400)
    await save_submission(req.name.strip(), req.email.strip())
    logger.info(f"New submission: {req.name} <{req.email}>")
    return {"success": True, "message": f"Thanks {req.name}! 🎁 Gift on its way!"}


@app.get("/emails")
async def list_emails():
    submissions = await get_all_submissions()
    return {"count": len(submissions), "submissions": submissions}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
