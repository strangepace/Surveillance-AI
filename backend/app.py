# backend_v3/app.py
"""
FastAPI app exposing the analyzer pipeline as a REST API.
Enhanced with error handling and Colab compatibility.
"""

# --- CRITICAL: Setup logging FIRST, before anything else ---
from logging_config import setup_logging
LOG_PATH = setup_logging()  # must be first side-effect

# --- CRITICAL: Setup FFmpeg environment automatically ---
from utils.ffmpeg import setup_ffmpeg_environment
ffmpeg_available = setup_ffmpeg_environment()

import os
import json
import shutil
import logging
import traceback
import time
import asyncio
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Import our new modules
from error_handler import error_handler, ErrorType
from colab_compat import colab_compat
from analyzer import analyze_video  # Use the main analyzer for model routing
from google_engine import analyze_with_google  # Google Video Intelligence placeholder

logger = logging.getLogger("analyzer_api")

# --- Initialize Colab compatibility ---
colab_compat.log_environment()

# --- Configurable paths using Colab compatibility ---
UPLOAD_DIR = colab_compat.get_uploads_dir()
RESULTS_DIR = colab_compat.get_results_dir()
PREVIEWS_DIR = os.path.join(RESULTS_DIR, "previews")
JSON_DIR = os.path.join(RESULTS_DIR, "json")
LOGS_DIR = colab_compat.get_logs_dir()
DOWNLOADS_DIR = os.path.join(RESULTS_DIR, "downloads")

# --- Ensure required folders exist ---
for d in [UPLOAD_DIR, RESULTS_DIR, PREVIEWS_DIR, JSON_DIR, LOGS_DIR, DOWNLOADS_DIR]:
    colab_compat.ensure_directory(d)

# Log startup immediately
logger.info("=" * 60)
logger.info("SURVEILLANCE AI BACKEND STARTING - DIAGNOSTIC MODE")
logger.info("=" * 60)
logger.info(f"Log file: {LOG_PATH}")
logger.info("Log level: DEBUG")
logger.info("=" * 60)

# --- FFmpeg Status Logging ---
if ffmpeg_available:
    logger.info("✅ FFmpeg environment configured successfully")
else:
    logger.warning("⚠️  FFmpeg not available - preview generation will be limited")
    logger.info("💡 To enable full functionality, install FFmpeg or ensure bundled binaries are present")

# --- FastAPI app ---
app = FastAPI(
    title="Surveillance AI Analyzer API", 
    version="3.1.0",
    description="AI-powered video surveillance system with real-time analysis and live alerts",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Device detection at startup ---
import torch
device_config = {"auto_detect": True, "force_cpu": False, "log_device": True}
if device_config.get("force_cpu"):
    startup_device = "cpu"
elif device_config.get("auto_detect") and torch.cuda.is_available():
    startup_device = "cuda"
    gpu_name = torch.cuda.get_device_name(0)
    logger.info(f"Server starting with GPU: {gpu_name}")
else:
    startup_device = "cpu"
    logger.info(f"Server starting with CPU")

# Log environment info
logger.info(f"Environment: {'Colab' if colab_compat.is_colab() else 'Local'}")
logger.info(f"Upload directory: {UPLOAD_DIR}")
logger.info(f"Results directory: {RESULTS_DIR}")
logger.info(f"Logs directory: {LOGS_DIR}")

# --- CORS for frontend integration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:8080", 
        "http://127.0.0.1:8080",  # DIAGNOSTIC: Added explicit IP address
        "https://*.lovable.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory storage for job tracking ---
task_storage: Dict[str, Dict[str, Any]] = {}
export_storage: Dict[str, Dict[str, Any]] = {}
alert_storage: Dict[str, Dict[str, Any]] = {}
active_websockets: List = []

# --- Background task function ---
async def process_video_analysis(video_id: str, video_path: str, prompts: List[str], model: str):
    """Background task to process video analysis"""
    try:
        # Update status to running
        task_storage[video_id].update({
            "status": "running",
            "progress": 10
        })
        
        logger.info(f"Starting background analysis for video {video_id}")
        
        # Run analysis based on model parameter
        if model.lower() == "clip":
            logger.info(f"Starting CLIP analysis for {video_id}...")
            results, json_path = await analyze_video(
                video_path=video_path, 
                prompts=prompts, 
                output_dir=RESULTS_DIR
            )
        elif model.lower() == "google":
            logger.info(f"Starting Google analysis for {video_id}...")
            results, json_path = await analyze_with_google(
                video_path=video_path, 
                prompts=prompts, 
                output_dir=RESULTS_DIR
            )
        else:
            raise Exception(f"Unsupported model: {model}")
        
        # Update progress
        task_storage[video_id].update({
            "status": "running",
            "progress": 90
        })
        
        # Handle results
        if isinstance(results, dict):
            # New format with alert summary
            detections = results.get("detections", [])
            alert_summary = results.get("alert_summary", {})
            analysis_timestamp = results.get("analysis_timestamp", "")
            
            # Convert local preview paths to full URLs for frontend
            for detection in detections:
                if "preview_clip" in detection and detection["preview_clip"]:
                    # Convert local path to full URL
                    original_path = detection["preview_clip"]
                    logger.info(f"Converting preview path: {original_path}")
                    
                    # Always extract just the filename, regardless of path format
                    filename = os.path.basename(original_path)
                    logger.info(f"Extracted filename: {filename}")
                    
                    # Normalize path separators for web URLs
                    filename = filename.replace("\\", "/")
                    
                    # Convert to full URL
                    final_url = f"http://127.0.0.1:8000/results/previews/{filename}"
                    logger.info(f"Converted to: {final_url}")
                    detection["preview_clip"] = final_url
                    
                    # Add format-specific preview paths for dual-source support
                    base_name = os.path.splitext(filename)[0]
                    mp4_filename = f"{base_name}.mp4"
                    webm_filename = f"{base_name}.webm"
                    
                    # Check if both formats exist and add them
                    mp4_path = os.path.join("results", "previews", mp4_filename)
                    webm_path = os.path.join("results", "previews", webm_filename)
                    
                    if os.path.exists(mp4_path):
                        detection["preview_clip_mp4"] = f"http://127.0.0.1:8000/results/previews/{mp4_filename}"
                        logger.info(f"Added MP4 preview: {detection['preview_clip_mp4']}")
                    
                    if os.path.exists(webm_path):
                        detection["preview_clip_webm"] = f"http://127.0.0.1:8000/results/previews/{webm_filename}"
                        logger.info(f"Added WebM preview: {detection['preview_clip_webm']}")
                    
                    # Ensure primary preview_clip points to the best available format
                    if "preview_clip_mp4" in detection:
                        detection["preview_clip"] = detection["preview_clip_mp4"]
                    elif "preview_clip_webm" in detection:
                        detection["preview_clip"] = detection["preview_clip_webm"]
            
            # Create live alerts for high-confidence detections
            for detection in detections:
                if detection.get("confidence", 0) > 0.5:  # DIAGNOSTIC: was 0.7, now 0.5 for testing
                    alert = create_alert_from_detection(detection)
                    alert_storage[alert.alertId] = alert.dict()
                    send_alert_via_websocket(alert)
            
            response_data = {
                "status": "success",
                "video_id": video_id,
                "results": detections,
                "alert_summary": alert_summary,
                "analysis_timestamp": analysis_timestamp,
                "json_path": json_path.replace("\\", "/")
            }
        else:
            # Legacy format - just detections
            response_data = {
                "status": "success",
                "video_id": video_id,
                "results": results,
                "json_path": json_path.replace("\\", "/")
            }
        
        # Store complete results and update status
        task_storage[video_id].update({
            "status": "complete",
            "progress": 100,
            "etaSeconds": 0,
            "results": response_data
        })
        
        logger.info(f"Background analysis completed for video {video_id}")
        
    except Exception as e:
        logger.error(f"Background analysis failed for video {video_id}: {str(e)}")
        task_storage[video_id].update({
            "status": "error",
            "progress": 0,
            "error": str(e)
        })

# --- Pydantic models for API responses ---
class StatusResponse(BaseModel):
    status: str  # "queued" | "running" | "complete" | "error"
    progress: int  # 0..100
    etaSeconds: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "running",
                "progress": 45,
                "etaSeconds": 30
            }
        }

class HealthResponse(BaseModel):
    status: str
    version: str
    api_version: str
    environment: str
    device: str
    gpu: Optional[str] = None
    modelCache: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "3.1.0",
                "api_version": "3.1.0",
                "environment": "local",
                "device": "cuda",
                "gpu": "NVIDIA GeForce RTX 3080",
                "modelCache": True
            }
        }

class ExportResponse(BaseModel):
    exportId: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "exportId": "exp_12345678"
            }
        }

class ExportStatusResponse(BaseModel):
    status: str  # "queued" | "running" | "complete" | "error"
    progress: Optional[int] = None
    url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "complete",
                "progress": 100,
                "url": "/downloads/exp_12345678.zip"
            }
        }

class Alert(BaseModel):
    alertId: str
    cameraId: str
    tsUnix: int
    timestamp: str
    labels: List[str]
    category: str
    confidence: float
    thumbnailUrl: Optional[str] = None
    clipUrl: Optional[str] = None
    location: Optional[str] = None
    pinned: bool = False
    acknowledged: bool = False
    note: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "alertId": "alrt_123",
                "cameraId": "CAM001",
                "tsUnix": 1723212345,
                "timestamp": "12:34:56",
                "labels": ["person", "red jacket"],
                "category": "people",
                "confidence": 0.92,
                "thumbnailUrl": "/previews/alrt_123.jpg",
                "clipUrl": "/previews/alrt_123.mp4",
                "location": "Main Entrance",
                "pinned": False,
                "acknowledged": False,
                "note": None
            }
        }

class LiveEvent(BaseModel):
    type: str
    data: Alert
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "alert",
                "data": {
                    "alertId": "alrt_123",
                    "cameraId": "CAM001",
                    "tsUnix": 1723212345,
                    "timestamp": "12:34:56",
                    "labels": ["person", "red jacket"],
                    "category": "people",
                    "confidence": 0.92,
                    "thumbnailUrl": "/previews/alrt_123.jpg",
                    "clipUrl": "/previews/alrt_123.mp4",
                    "location": "Main Entrance",
                    "pinned": False,
                    "acknowledged": False,
                    "note": None
                }
            }
        }

class AlertsResponse(BaseModel):
    alerts: List[Alert]
    total: int
    page: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "alerts": [],
                "total": 0,
                "page": 1,
                "limit": 200
            }
        }

class ActionRequest(BaseModel):
    alertId: str

class AcknowledgeRequest(BaseModel):
    alertId: str
    acknowledged: bool

class PinRequest(BaseModel):
    alertId: str
    pinned: bool

class NoteRequest(BaseModel):
    alertId: str
    note: str

class LiveExportRequest(BaseModel):
    alertId: str

class ActionResponse(BaseModel):
    ok: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "message": "Action completed successfully"
            }
        }

@app.get("/health", tags=["Health"])
def health():
    """Enhanced health check endpoint with device and model information."""
    return HealthResponse(
        status="ok",
        version="3.1.0",
        api_version="3.1.0",
        environment="colab" if colab_compat.is_colab() else "local",
        device=startup_device,
        gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        modelCache=True  # Assuming model is cached
    )

@app.get("/status", tags=["Status"])
async def get_status(jobId: str = Query(..., description="Job ID to check status")):
    """Get the status of a video analysis job."""
    if jobId not in task_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = task_storage[jobId]
    return StatusResponse(
        status=job.get("status", "queued"),
        progress=job.get("progress", 0),
        etaSeconds=job.get("etaSeconds")
    )

@app.get("/results", tags=["Results"])
async def get_results(jobId: str = Query(..., description="Job ID to fetch results")):
    """Get the results of a completed video analysis job."""
    if jobId not in task_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = task_storage[jobId]
    if job.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    return job.get("results", {})

@app.post("/export/clips", tags=["Export"])
async def export_clips(jobId: str = Query(..., description="Job ID to export")):
    """Start an export job for video clips."""
    if jobId not in task_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    export_id = f"exp_{uuid4().hex[:8]}"
    export_storage[export_id] = {
        "jobId": jobId,
        "status": "queued",
        "progress": 0,
        "created_at": datetime.now().isoformat()
    }
    
    # Simulate async export process
    asyncio.create_task(process_export(export_id))
    
    return ExportResponse(exportId=export_id)

@app.get("/export/status", tags=["Export"])
async def get_export_status(exportId: str = Query(..., description="Export ID to check status")):
    """Get the status of an export job."""
    if exportId not in export_storage:
        raise HTTPException(status_code=404, detail="Export not found")
    
    export = export_storage[exportId]
    return ExportStatusResponse(
        status=export.get("status", "queued"),
        progress=export.get("progress", 0),
        url=export.get("url")
    )

# --- Live Alert System ---
def generate_alert_id() -> str:
    return f"alrt_{uuid4().hex[:8]}"

def format_timestamp(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

def categorize_labels(labels: List[str]) -> str:
    """Categorize labels into alert categories."""
    people_keywords = ["person", "man", "woman", "child", "people"]
    vehicle_keywords = ["car", "truck", "bike", "motorcycle", "vehicle"]
    weapon_keywords = ["gun", "knife", "weapon"]
    fire_keywords = ["fire", "smoke", "flame"]
    
    label_lower = [l.lower() for l in labels]
    
    if any(kw in label_lower for kw in people_keywords):
        return "people"
    elif any(kw in label_lower for kw in vehicle_keywords):
        return "vehicle"
    elif any(kw in label_lower for kw in weapon_keywords):
        return "weapon"
    elif any(kw in label_lower for kw in fire_keywords):
        return "fire"
    else:
        return "activity"

def create_alert_from_detection(detection: Dict[str, Any], camera_id: str = "CAM001") -> Alert:
    """Create an alert from a detection result."""
    alert_id = generate_alert_id()
    ts_unix = int(time.time())
    
    return Alert(
        alertId=alert_id,
        cameraId=camera_id,
        tsUnix=ts_unix,
        timestamp=format_timestamp(ts_unix),
        labels=detection.get("labels", []),
        category=categorize_labels(detection.get("labels", [])),
        confidence=detection.get("confidence", 0.0),
        thumbnailUrl=f"/previews/{alert_id}.jpg",
        clipUrl=f"/previews/{alert_id}.mp4",
        location=None,
        pinned=False,
        acknowledged=False,
        note=None
    )

async def broadcast_event(event: LiveEvent):
    """Broadcast event to all connected WebSockets."""
    for websocket in active_websockets:
        try:
            await websocket.send_text(event.json())
        except Exception as e:
            logger.error(f"Failed to send to WebSocket: {e}")
            active_websockets.remove(websocket)

def send_alert_via_websocket(alert: Alert):
    """Send alert via WebSocket."""
    event = LiveEvent(type="alert", data=alert)
    asyncio.create_task(broadcast_event(event))

@app.get("/live/alerts", tags=["Live", "Alerts"])
async def get_live_alerts(
    cameraId: Optional[str] = Query(None, description="Filter by camera ID"),
    since: Optional[int] = Query(None, description="Unix timestamp to filter since"),
    limit: int = Query(200, description="Maximum number of alerts to return"),
    page: int = Query(1, description="Page number")
):
    """Get live alert history."""
    alerts = list(alert_storage.values())
    
    # Apply filters
    if cameraId:
        alerts = [a for a in alerts if a.get("cameraId") == cameraId]
    if since:
        alerts = [a for a in alerts if a.get("tsUnix", 0) >= since]
    
    # Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_alerts = alerts[start_idx:end_idx]
    
    return AlertsResponse(
        alerts=[Alert(**alert) for alert in paginated_alerts],
        total=len(alerts),
        page=page,
        limit=limit
    )

@app.post("/live/acknowledge", tags=["Live", "Actions"])
async def acknowledge_alert(request: AcknowledgeRequest):
    """Acknowledge or un-acknowledge an alert."""
    if request.alertId not in alert_storage:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert_storage[request.alertId]["acknowledged"] = request.acknowledged
    return ActionResponse(ok=True, message="Alert acknowledged successfully")

@app.post("/live/pin", tags=["Live", "Actions"])
async def pin_alert(request: PinRequest):
    """Pin or unpin an alert."""
    if request.alertId not in alert_storage:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert_storage[request.alertId]["pinned"] = request.pinned
    return ActionResponse(ok=True, message="Alert pinned successfully")

@app.post("/live/note", tags=["Live", "Actions"])
async def add_note_to_alert(request: NoteRequest):
    """Add or update a note on an alert."""
    if request.alertId not in alert_storage:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert_storage[request.alertId]["note"] = request.note
    return ActionResponse(ok=True, message="Note added successfully")

@app.post("/live/export", tags=["Live", "Export"])
async def export_alert_clip(request: LiveExportRequest):
    """Export an alert's clip."""
    if request.alertId not in alert_storage:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    export_id = f"exp_{uuid4().hex[:8]}"
    export_storage[export_id] = {
        "alertId": request.alertId,
        "status": "queued",
        "progress": 0,
        "created_at": datetime.now().isoformat()
    }
    
    # Simulate async export process
    asyncio.create_task(process_alert_export(export_id))
    
    return ExportResponse(exportId=export_id)

@app.get("/live/export/status", tags=["Live", "Export"])
async def get_live_export_status(exportId: str = Query(..., description="Export ID to check status")):
    """Get the status of a live alert export."""
    if exportId not in export_storage:
        raise HTTPException(status_code=404, detail="Export not found")
    
    export = export_storage[exportId]
    return ExportStatusResponse(
        status=export.get("status", "queued"),
        progress=export.get("progress", 0),
        url=export.get("url")
    )

@app.post("/live/demo/generate", tags=["Live", "Demo"])
async def generate_demo_alert():
    """Generate a demo alert for testing."""
    demo_alert = Alert(
        alertId=generate_alert_id(),
        cameraId="CAM001",
        tsUnix=int(time.time()),
        timestamp=format_timestamp(int(time.time())),
        labels=["person", "red jacket"],
        category="people",
        confidence=0.92,
        thumbnailUrl="/previews/demo.jpg",
        clipUrl="/previews/demo.mp4",
        location="Main Entrance",
        pinned=False,
        acknowledged=False,
        note=None
    )
    
    alert_storage[demo_alert.alertId] = demo_alert.dict()
    send_alert_via_websocket(demo_alert)
    
    return ActionResponse(ok=True, message="Demo alert generated")

# --- WebSocket support ---
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket, cameraId: Optional[str] = None):
    """WebSocket endpoint for live alert streaming."""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# --- Static file serving ---
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")
# --- Background tasks ---
async def process_export(export_id: str):
    """Process an export job asynchronously."""
    export = export_storage[export_id]
    
    # Simulate processing time
    for progress in range(0, 101, 10):
        export["progress"] = progress
        export["status"] = "running" if progress < 100 else "complete"
        await asyncio.sleep(0.5)
    
    # Generate download URL
    export["url"] = f"/downloads/{export_id}.zip"
    export_storage[export_id] = export

async def process_alert_export(export_id: str):
    """Process an alert export job asynchronously."""
    export = export_storage[export_id]
    
    # Simulate processing time
    for progress in range(0, 101, 10):
        export["progress"] = progress
        export["status"] = "running" if progress < 100 else "complete"
        await asyncio.sleep(0.3)
    
    # Generate download URL
    export["url"] = f"/downloads/alert_{export_id}.mp4"
    export_storage[export_id] = export

# --- Cleanup task ---
@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    # Start cleanup task
    asyncio.create_task(cleanup_task())

async def cleanup_task():
    """Periodic cleanup of old exports."""
    while True:
        try:
            current_time = datetime.now()
            to_delete = []
            
            for export_id, export in export_storage.items():
                created_at = datetime.fromisoformat(export.get("created_at", ""))
                if (current_time - created_at).total_seconds() > 3600:  # 1 hour
                    to_delete.append(export_id)
            
            for export_id in to_delete:
                del export_storage[export_id]
                logger.info(f"Cleaned up old export: {export_id}")
            
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
        
        await asyncio.sleep(300)  # Run every 5 minutes

class AnalyzeRequest(BaseModel):
    video_path: str
    prompts: List[str]
    model: Optional[str] = "clip"

@app.post("/analyze", tags=["Analyze"])
async def analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompts: str = Form(...),
    model: str = Form("clip")  # Default to "clip" if not provided
):
    """
    Analyze uploaded video with given prompts (file upload API).
    Enhanced with comprehensive error handling and job tracking.
    """
    logger.info(f"Starting analysis request")
    logger.info(f"   Model: {model}")
    logger.info(f"   File: {file.filename}")
    
    try:
        # Validate file
        if not file.filename:
            error_response = error_handler.handle_validation_error(
                Exception("No filename provided"), "filename", file.filename
            )
            return JSONResponse(status_code=400, content=error_response)
        
        # Validate file type
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in valid_extensions:
            error_response = error_handler.handle_validation_error(
                Exception(f"Unsupported file format: {file_ext}"), "file_extension", file_ext
            )
            return JSONResponse(status_code=400, content=error_response)
        
        # Save uploaded file with error handling
        video_id = f"video_{uuid4().hex[:8]}"
        filename = f"{video_id}.mp4"
        upload_path = os.path.join(UPLOAD_DIR, filename)
        
        try:
            with open(upload_path, "wb") as out_file:
                shutil.copyfileobj(file.file, out_file)
            logger.info(f"File saved: {upload_path}")
        except Exception as e:
            error_response = error_handler.handle_file_io_error(e, upload_path, "save_upload")
            return JSONResponse(status_code=500, content=error_response)
        
        # Validate video file
        is_valid, validation_msg = error_handler.validate_video_file(upload_path)
        if not is_valid:
            error_response = error_handler.handle_validation_error(
                Exception(validation_msg), "video_file", upload_path
            )
            return JSONResponse(status_code=400, content=error_response)
        
        # Parse and validate prompts
        prompt_list = [p.strip() for p in prompts.split(",") if p.strip()]
        is_valid, validation_msg = error_handler.validate_prompts(prompt_list)
        if not is_valid:
            error_response = error_handler.handle_validation_error(
                Exception(validation_msg), "prompts", prompt_list
            )
            return JSONResponse(status_code=400, content=error_response)
        
        logger.info(f"Prompts validated: {prompt_list}")
        logger.info(f"Using model: {model}")
        
        # Initialize job tracking
        task_storage[video_id] = {
            "status": "queued",
            "progress": 0,
            "etaSeconds": None,
            "created_at": datetime.now().isoformat()
        }
        
        # Start background analysis task
        background_tasks.add_task(
            process_video_analysis,
            video_id=video_id,
            video_path=upload_path, 
            prompts=prompt_list, 
            model=model
        )
        
        # Return immediately with job ID
        return {
            "status": "queued",
            "video_id": video_id,
            "message": "Analysis started in background"
        }
            
    except Exception as e:
        # Catch any unexpected errors
        error_response = error_handler.create_error_response(e, ErrorType.UNKNOWN, {
            "endpoint": "/analyze",
            "file": file.filename if file else None
        })
        return JSONResponse(status_code=500, content=error_response)

# --- Preserve old form endpoint for testing ---
@app.post("/analyze_form", tags=["Analyze"])
async def analyze_form(
    file: UploadFile = File(...),
    prompts: str = Form(...)
):
    """
    Analyze uploaded video with given prompts (legacy form API).
    """
    # Reuse the main analyze function logic
    return await analyze(file=file, prompts=prompts, model="clip")

@app.get("/environment", tags=["Health"])
def get_environment():
    """Get environment information."""
    return colab_compat.get_environment_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
