import logging
import os
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Set
import asyncio
import json
import shutil

from app.config import load_config
from app.audio import AudioRecorder
from app.transcriber import WhisperTranscriber
from app.summarizer import OllamaSummarizer
from app.storage import StorageManager
from app.database import DatabaseManager
from app.hardware import detect_and_configure_gpu
from app.preference_learner import PreferenceLearner
from fastapi.responses import FileResponse
import uuid
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Setup logging
from app.logging_utils import configure_logging
configure_logging()
logger = logging.getLogger("medrec-api")

app = FastAPI(title="GI Scribe API")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"status": "error", "detail": "An unexpected error occurred. Please contact IT support."})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(status_code=422, content={"status": "error", "detail": "Invalid request parameters."})

# Enable CORS for local Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
config = load_config()
gpu_index = detect_and_configure_gpu()
recorder = AudioRecorder(config.audio)
transcriber = WhisperTranscriber(config.whisper)
summarizer = OllamaSummarizer(config.summarizer)
storage = StorageManager(config.storage)
db = DatabaseManager("medrec.db")
learner = PreferenceLearner(db)

class UpdateSessionRequest(BaseModel):
    transcript: Optional[str] = None
    summary: Optional[str] = None
    label: Optional[str] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

class StatusResponse(BaseModel):
    is_recording: bool
    last_transcript: Optional[str] = None
    last_summary: Optional[str] = None
    gpu_label: str

@app.get("/status")
async def get_status():
    return {
        "is_recording": recorder.is_recording if hasattr(recorder, 'is_recording') else False,
        "gpu_label": f"RTX 3060 (Index {gpu_index})" if gpu_index is not None else "CPU",
        "summarizer_ready": True
    }

@app.post("/record/start")
async def start_recording():
    temp_dir = Path(config.storage.root) / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    session_uuid = str(uuid.uuid4())
    audio_path = temp_dir / f"{session_uuid}.wav"
    
    try:
        recorder.start(audio_path)
        logger.info(f"Started recording session {session_uuid} to {audio_path}")
        return {"status": "started", "uuid": session_uuid, "path": str(audio_path)}
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record/stop/{session_uuid}")
async def stop_recording(session_uuid: str, background_tasks: BackgroundTasks):
    try:
        recorder.stop()
        audio_path = recorder._output_path
        file_size = recorder.last_file_size
        
        logger.info(f"Stopped recording {session_uuid}. Size: {file_size}")
        
        if audio_path and audio_path.exists() and (file_size or 0) > 1024:
            background_tasks.add_task(process_session, session_uuid, audio_path)
            return {"status": "processing", "uuid": session_uuid}
        
        return {"status": "stopped", "detail": "Empty recording"}
    except Exception as e:
        logger.error(f"Failed to stop recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_session(session_uuid: str, audio_path: Path):
    """Background task for transcription, summarization, and DB storage."""
    loop = asyncio.get_running_loop()
    try:
        def on_progress(text: str, percentage: int = 0):
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(json.dumps({"type": "transcript", "text": text, "percentage": percentage, "uuid": session_uuid})),
                loop
            )

        logger.info(f"Transcription starting for {session_uuid}")
        # Run synchronous transcription in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(
            transcriber.transcribe, 
            audio_path, 
            progress_cb=on_progress
        )
        
        logger.info("Summarization starting")
        await manager.broadcast(json.dumps({
            "type": "status", 
            "text": "Synthesizing Clinical Note...", 
            "uuid": session_uuid
        }))
        
        # Run synchronous summarization in a thread
        summary_obj = await asyncio.to_thread(summarizer.summarize, result.text)
        summary_text = summary_obj.summary if hasattr(summary_obj, "summary") else str(summary_obj)
        
        # Persist files
        artifacts = storage.persist(
            audio_file=audio_path,
            transcript=result.text,
            summary=summary_text,
            metadata={"uuid": session_uuid}
        )
        
        # Save to DB
        db.add_session(
            uuid=session_uuid,
            audio_path=str(artifacts.audio_path),
            transcript=result.text,
            summary=summary_text,
            metadata={
                "transcriber_runtime_s": result.runtime_s,
                "summarizer_runtime_s": getattr(summary_obj, "runtime_s", 0) if hasattr(summary_obj, "runtime_s") else 0,
                "whisper_command": result.command
            }
        )
        
        await manager.broadcast(json.dumps({
            "type": "summary", 
            "text": summary_text,
            "uuid": session_uuid
        }))
        logger.info(f"Session {session_uuid} complete and persisted.")
        
    except Exception as e:
        logger.error(f"Session {session_uuid} failed: {e}")
        await manager.broadcast(json.dumps({"type": "error", "uuid": session_uuid, "detail": str(e)}))

@app.get("/sessions")
async def list_sessions():
    return db.list_sessions()

@app.get("/sessions/{session_uuid}")
async def get_session(session_uuid: str):
    session = db.get_session(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
@app.delete("/sessions/{session_uuid}")
async def delete_session(session_uuid: str):
    session = db.get_session(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Optional: Delete files on disk
    if session.get("audio_path"):
        p = Path(session["audio_path"]).parent
        if p.exists() and "local_storage" in str(p):
            import shutil
            shutil.rmtree(p, ignore_errors=True)

    db.delete_session(session_uuid)
    return {"status": "success"}

@app.get("/sessions/{session_uuid}/audio")
async def get_session_audio(session_uuid: str):
    session = db.get_session(session_uuid)
    if not session or not session["audio_path"]:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    path = Path(session["audio_path"])
    if not path.exists():
         raise HTTPException(status_code=404, detail="Audio file missing on disk")
    
    return FileResponse(path, media_type="audio/wav")

@app.post("/sessions/{session_uuid}/feedback")
async def submit_feedback(session_uuid: str, req: UpdateSessionRequest):
    session = db.get_session(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if req.summary:
        db.add_feedback(session_uuid, "summary", session["summary"], req.summary)
        # Self-Learning: extract preferences from the correction
        learned = learner.learn_from_correction(session["summary"] or "", req.summary)
        db.update_session(session_uuid, summary=req.summary)
        # Update file too
        if session.get("audio_path"):
            (Path(session["audio_path"]).parent / "summary.txt").write_text(req.summary, encoding="utf-8")
        
    if req.transcript:
        db.add_feedback(session_uuid, "transcript", session["transcript"], req.transcript)
        db.update_session(session_uuid, transcript=req.transcript)
        # Update file too
        if session.get("audio_path"):
            (Path(session["audio_path"]).parent / "transcript.txt").write_text(req.transcript, encoding="utf-8")
        
    return {"status": "success", "preferences_learned": len(learned) if req.summary else 0}

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload an audio file for transcription and summarization."""
    try:
        session_uuid = str(uuid.uuid4())
        # Save uploaded file to local_storage
        upload_dir = Path("local_storage") / session_uuid
        upload_dir.mkdir(parents=True, exist_ok=True)
        audio_path = upload_dir / file.filename
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"Audio uploaded: {file.filename} -> {audio_path} ({audio_path.stat().st_size} bytes)")
        
        # Kick off transcription + summarization in background
        background_tasks.add_task(process_session, session_uuid, audio_path)
        
        return {"status": "processing", "uuid": session_uuid, "filename": file.filename}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/sessions/{session_uuid}/summarize")
async def summarize_session(session_uuid: str):
    session = db.get_session(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    try:
        logger.info(f"Re-summarizing session {session_uuid}")
        new_summary_obj = summarizer.summarize(session["transcript"])
        new_summary = new_summary_obj.summary if hasattr(new_summary_obj, "summary") else str(new_summary_obj)
        db.update_session(session_uuid, summary=new_summary)
        
        # Update file too
        if session["audio_path"]:
            (Path(session["audio_path"]).parent / "summary.txt").write_text(new_summary, encoding="utf-8")
            
        return {"status": "success", "summary": new_summary}
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Adaptive Learning Endpoints ──────────────────────────────────

@app.patch("/sessions/{session_uuid}/label")
async def update_session_label(session_uuid: str, req: UpdateSessionRequest):
    if req.label is None:
        raise HTTPException(status_code=400, detail="Label is required")
    db.update_session_label(session_uuid, req.label)
    return {"status": "success", "label": req.label}

@app.post("/sessions/{session_uuid}/approve")
async def approve_session(session_uuid: str):
    """Approve a summary as-is — positive reinforcement for the current style."""
    session = db.get_session(session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Positive reinforcement: boost confidence of all existing preferences
    prefs = db.get_preferences()
    for p in prefs:
        db.upsert_preference(p["category"], p["preference_key"], p["preference_value"])
    return {"status": "approved", "preferences_reinforced": len(prefs)}

@app.get("/preferences")
async def get_preferences():
    """Return all learned physician preferences and feedback stats."""
    prefs = db.get_preferences()
    return {
        "preferences": prefs,
        "feedback_count": db.get_feedback_count(),
        "preference_count": len(prefs),
    }

@app.post("/preferences/reset")
async def reset_learned_preferences():
    """Reset all learned preferences (start fresh)."""
    count = db.reset_preferences()
    return {"status": "reset", "preferences_deleted": count}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def stream_transcription():
    """Mock stream - will connect to real transcriber later."""
    while True:
        if recorder.is_recording:
             # This is where we'd get live chunks from Whisper
             pass
        await asyncio.sleep(0.5)
