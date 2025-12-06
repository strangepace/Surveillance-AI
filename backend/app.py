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
import hashlib
import subprocess
import re
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Import our new modules
from error_handler import error_handler, ErrorType
from colab_compat import colab_compat
from analyzer import analyze_video  # Use the main analyzer for model routing
from config_loader import load_clip_config
from media_registry import (
    init_registry,
    make_media_id,
    upsert_media,
    get_by_id as registry_get_by_id,
    find_by_key as registry_find_by_key,
    touch as registry_touch,
    total_size_gb as registry_total_size_gb,
    evict_if_needed as registry_evict_if_needed,
)
from utils.preview_merge import (
    merge_detections_by_label,
    pad_and_cap,
    seconds_to_ts,
    get_video_duration_seconds,
    ffmpeg_cut_segment,
    sanitize_label,
)
from utils.time_utils import validate_time_window, seconds_to_hms
from utils.ffmpeg import clip_video_segment, get_video_info, has_ffmpeg
from google_engine import analyze_with_google  # Google Video Intelligence placeholder
from models.provenance import provenance_db, create_provenance_record

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

# --- URL Ingestion directories ---
URL_TMP_DIR = os.path.join(UPLOAD_DIR, "url_tmp")

# --- Ensure required folders exist ---
for d in [UPLOAD_DIR, RESULTS_DIR, PREVIEWS_DIR, JSON_DIR, LOGS_DIR, DOWNLOADS_DIR, URL_TMP_DIR]:
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

# --- Media serving middleware ---
class MediaServingMiddleware(BaseHTTPMiddleware):
    """Middleware to add proper headers for media serving."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Load media serving config
        try:
            cfg = load_clip_config()
            media_config = cfg.get("media_serving", {})
        except Exception:
            media_config = {}
        
        # Add Accept-Ranges header and ensure correct Content-Type for video files
        if request.url.path.endswith(('.mp4', '.webm', '.avi', '.mov', '.mkv')):
            if media_config.get("accept_ranges", True):
                response.headers["Accept-Ranges"] = "bytes"
            
            # Ensure correct Content-Type for video files
            if request.url.path.endswith('.mp4'):
                response.headers["Content-Type"] = "video/mp4"
            elif request.url.path.endswith('.webm'):
                response.headers["Content-Type"] = "video/webm"
            elif request.url.path.endswith('.avi'):
                response.headers["Content-Type"] = "video/x-msvideo"
            elif request.url.path.endswith('.mov'):
                response.headers["Content-Type"] = "video/quicktime"
            elif request.url.path.endswith('.mkv'):
                response.headers["Content-Type"] = "video/x-matroska"
        
        # Add CORS headers for media files if configured
        cors_allowed = media_config.get("cors_allowed", [])
        if cors_allowed and request.url.path.startswith(('/uploads/', '/results/', '/downloads/')):
            origin = request.headers.get("origin")
            if origin in cors_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Range, Content-Range"
        
        return response

app.add_middleware(MediaServingMiddleware)

# --- In-memory storage for job tracking ---
task_storage: Dict[str, Dict[str, Any]] = {}
export_storage: Dict[str, Dict[str, Any]] = {}
alert_storage: Dict[str, Dict[str, Any]] = {}
active_websockets: List = []

# --- Background task function ---
async def process_video_analysis(video_id: str, video_path: str, prompts: List[str], model: str, start_ts: Optional[str] = None, end_ts: Optional[str] = None):
    """Background task to process video analysis"""
    try:
        # Update status to running
        task_storage[video_id].update({
            "status": "running",
            "progress": 10
        })
        
        logger.info(f"Starting background analysis for video {video_id}")
        
        # Handle analysis window if provided
        base_offset_seconds = 0.0
        analysis_window = None
        analysis_video_path = video_path  # Default to full video
        
        if start_ts and end_ts:
            try:
                # Get video duration for validation
                video_duration = get_video_duration_seconds(video_path) or 0.0
                if video_duration <= 0:
                    raise Exception("Could not determine video duration")
                
                # Validate time window
                start_seconds, end_seconds = validate_time_window(start_ts, end_ts, video_duration)
                base_offset_seconds = start_seconds
                
                analysis_window = {
                    "start": start_ts,
                    "end": end_ts,
                    "offsetSeconds": base_offset_seconds
                }
                
                logger.info(f"Analysis window: {start_ts} to {end_ts} (offset: {base_offset_seconds}s)")
                
                # Create clipped video for analysis
                clipped_video_path = video_path.replace('.mp4', f'_clipped_{video_id}.mp4')
                logger.info(f"Creating clipped video: {clipped_video_path}")
                
                if clip_video_segment(video_path, start_seconds, end_seconds, clipped_video_path):
                    logger.info(f"Video clipped successfully, analyzing clipped version")
                    # Use clipped video for analysis
                    analysis_video_path = clipped_video_path
                else:
                    logger.warning(f"Video clipping failed, analyzing full video with offset")
                    # Fallback to full video with offset
                    analysis_video_path = video_path
                
            except Exception as e:
                logger.error(f"Invalid time window: {e}")
                raise Exception(f"Invalid time window: {e}")
        
        # Run analysis based on model parameter
        if model.lower() == "clip":
            logger.info(f"Starting CLIP analysis for {video_id}...")
            results, json_path = await analyze_video(
                video_path=analysis_video_path, 
                prompts=prompts, 
                output_dir=RESULTS_DIR,
                media_id=video_id  # Pass video_id as media_id for cached re-analysis
            )
        elif model.lower() == "google":
            logger.info(f"Starting Google analysis for {video_id}...")
            results, json_path = await analyze_with_google(
                video_path=analysis_video_path, 
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
            
            # Apply timestamp offset if analysis window was used
            if base_offset_seconds > 0:
                for detection in detections:
                    if "timestamp" in detection:
                        # Convert relative timestamp to absolute
                        rel_ts = detection["timestamp"]
                        # Parse relative timestamp and add offset
                        # This assumes timestamp is in HH:MM:SS format
                        try:
                            from utils.time_utils import parse_hms_to_seconds
                            rel_seconds = parse_hms_to_seconds(rel_ts)
                            abs_seconds = rel_seconds + base_offset_seconds
                            detection["timestamp"] = seconds_to_hms(abs_seconds)
                        except Exception as e:
                            logger.warning(f"Could not apply timestamp offset: {e}")
            
            # Convert local preview paths to full URLs for frontend (LEGACY PREVIEW SERVING - kept for fallback)
            cfg = load_clip_config()
            preview_generation_enabled = cfg.get("preview_generation", {}).get("enabled", False)
            
            for detection in detections:
                if "preview_clip" in detection and detection["preview_clip"]:
                    original_path = detection["preview_clip"]
                    
                    # Check if this is a virtual preview (new mode) or legacy file-based preview
                    if original_path.startswith("virtual_preview_"):
                        # Virtual preview mode - keep as-is for frontend to handle
                        logger.info(f"Virtual preview mode: {original_path}")
                        detection["preview_clip"] = original_path
                    elif preview_generation_enabled:
                        # Legacy mode - convert local path to full URL
                        logger.info(f"Converting legacy preview path: {original_path}")
                        
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
                    else:
                        # Preview generation disabled - use virtual preview
                        logger.info(f"Preview generation disabled, using virtual preview for: {original_path}")
                        detection["preview_clip"] = f"virtual_preview_{detection.get('timestamp', 'unknown').replace(':', '_')}"
            
            # --- Merged preview generation ---
            try:
                cfg = load_clip_config()
                pm = (cfg.get("preview_merge") or {}) if isinstance(cfg, dict) else {}
                if pm.get("enabled", True):
                    # Build simple detection list
                    simple = []
                    for d in detections:
                        simple.append({
                            "timestamp": d.get("timestamp"),
                            "labels": d.get("labels", []),
                            "confidence": float(d.get("confidence", 0.0)),
                        })
                    gap_s = float(pm.get("gap_seconds", 3))
                    runs_by_label = merge_detections_by_label(simple, gap_s)
                    video_len_s = get_video_duration_seconds(video_path) or 0.0
                    pad_pre = float(pm.get("pad_pre_seconds", 2))
                    pad_post = float(pm.get("pad_post_seconds", 2))
                    min_s = float(pm.get("min_seconds", 2))
                    max_s = float(pm.get("max_seconds", 30))

                    merged_outputs = []
                    
                    # Check if legacy preview generation is enabled
                    cfg = load_clip_config()
                    preview_generation_enabled = cfg.get("preview_generation", {}).get("enabled", False)
                    
                    if preview_generation_enabled:
                        # Legacy mode: generate actual preview files
                        out_dir = os.path.join(RESULTS_DIR, "previews", "merged")
                        os.makedirs(out_dir, exist_ok=True)
                    
                    for label, runs in runs_by_label.items():
                        runs2 = pad_and_cap(runs, pad_pre, pad_post, min_s, max_s, video_len_s)
                        for r in runs2:
                            start_s = float(r.get("start_s", 0.0))
                            end_s = float(r.get("end_s", start_s))
                            peak = float(r.get("peak_conf", 0.0))
                            
                            # Build base merged preview data (timestamps only)
                            merged_item = {
                                "label": label,
                                "start": seconds_to_ts(start_s),
                                "end": seconds_to_ts(end_s),
                                "duration": round(max(0.0, end_s - start_s), 3),
                                "confidence_peak": peak
                            }
                            
                            # Add URL only if legacy preview generation is enabled
                            if preview_generation_enabled:
                                safe = sanitize_label(label)
                                fname = f"{video_id}_{safe}_{int(start_s*1000)}_{int(end_s*1000)}.mp4"
                                out_path = os.path.join(out_dir, fname)
                                ok = ffmpeg_cut_segment(video_path, start_s, end_s, out_path)
                                if ok:
                                    merged_item["url"] = f"http://127.0.0.1:8000/results/previews/merged/{fname}"
                            
                            merged_outputs.append(merged_item)
                    
                    results["previewSets"] = results.get("previewSets", {})
                    results["previewSets"]["merged"] = merged_outputs
            except Exception as e:
                logger.error(f"Merged preview generation failed: {e}")

            # Create live alerts for high-confidence detections
            for detection in detections:
                if detection.get("confidence", 0) > 0.5:  # DIAGNOSTIC: was 0.7, now 0.5 for testing
                    alert = create_alert_from_detection(detection)
                    alert_storage[alert.alertId] = alert.dict()
                    send_alert_via_websocket(alert)
            
            # Build media info for virtual previews
            # Derive a web URL under /uploads preserving subdirectories (e.g., url_tmp)
            original_url = None
            try:
                if os.path.exists(video_path):
                    rel_path = os.path.relpath(video_path, UPLOAD_DIR)
                    # If rel_path starts with '..', the file is outside UPLOAD_DIR → no public URL
                    if not rel_path.startswith('..'):
                        rel_posix = rel_path.replace('\\', '/')
                        original_url = f"http://127.0.0.1:8000/uploads/{rel_posix}"
            except Exception:
                original_url = None

            media_info = {
                "media_id": video_id,
                "source": video_path,
                "original_url": original_url
            }
            
            # Add provenance data if available (for URL-ingested media)
            try:
                provenance_record = provenance_db.get_record(video_id)
                if provenance_record:
                    media_info.update({
                        "provenance": {
                            "source_url": provenance_record.source_url,
                            "provider": provenance_record.provider,
                            "title": provenance_record.title,
                            "channel": provenance_record.channel,
                            "duration_s": provenance_record.duration_s,
                            "window_start_s": provenance_record.window_start_s,
                            "window_end_s": provenance_record.window_end_s,
                            "created_utc": provenance_record.created_utc
                        }
                    })
                    logger.info(f"Added provenance data for media_id: {video_id}")
            except Exception as e:
                logger.warning(f"Could not retrieve provenance data for {video_id}: {e}")
            
            # Build previewSets with timestamps only (no server-generated files by default)
            preview_sets = results.get("previewSets", {})
            
            # If legacy preview generation is enabled, add micro preview URLs
            cfg = load_clip_config()
            preview_generation_enabled = cfg.get("preview_generation", {}).get("enabled", False)
            if preview_generation_enabled:
                # Add micro preview URLs to individual detections
                for detection in detections:
                    if "preview_clip" in detection and not detection["preview_clip"].startswith("virtual_preview_"):
                        detection["micro_preview_url"] = detection["preview_clip"]
            
            response_data = {
                "status": "success",
                "video_id": video_id,
                "results": detections,
                "alert_summary": alert_summary,
                "analysis_timestamp": analysis_timestamp,
                "json_path": json_path.replace("\\", "/"),
                "media": media_info,
                "previewSets": preview_sets
            }
            
            # Add analysis window if provided
            if analysis_window:
                response_data["analysisWindow"] = analysis_window
        else:
            # Legacy format - just detections
            # Build media info for virtual previews
            original_url = None
            try:
                if os.path.exists(video_path):
                    rel_path = os.path.relpath(video_path, UPLOAD_DIR)
                    if not rel_path.startswith('..'):
                        rel_posix = rel_path.replace('\\', '/')
                        original_url = f"http://127.0.0.1:8000/uploads/{rel_posix}"
            except Exception:
                original_url = None

            media_info = {
                "media_id": video_id,
                "source": video_path,
                "original_url": original_url
            }
            
            # Add provenance data if available (for URL-ingested media)
            try:
                provenance_record = provenance_db.get_record(video_id)
                if provenance_record:
                    media_info.update({
                        "provenance": {
                            "source_url": provenance_record.source_url,
                            "provider": provenance_record.provider,
                            "title": provenance_record.title,
                            "channel": provenance_record.channel,
                            "duration_s": provenance_record.duration_s,
                            "window_start_s": provenance_record.window_start_s,
                            "window_end_s": provenance_record.window_end_s,
                            "created_utc": provenance_record.created_utc
                        }
                    })
                    logger.info(f"Added provenance data for media_id: {video_id}")
            except Exception as e:
                logger.warning(f"Could not retrieve provenance data for {video_id}: {e}")
            
            response_data = {
                "status": "success",
                "video_id": video_id,
                "results": results,
                "json_path": json_path.replace("\\", "/"),
                "media": media_info,
                "previewSets": {}
            }
        
        # Store complete results and update status
        task_storage[video_id].update({
            "status": "complete",
            "progress": 100,
            "etaSeconds": 0,
            "results": response_data
        })
        
        # Mark analysis as completed in provenance record
        try:
            provenance_db.mark_analysis_completed(video_id)
            logger.info(f"Marked analysis completed for media_id: {video_id}")
        except Exception as e:
            logger.warning(f"Could not mark analysis completed for {video_id}: {e}")
        
        # Cleanup clipped video file if it was created
        if analysis_video_path != video_path and os.path.exists(analysis_video_path):
            try:
                os.remove(analysis_video_path)
                logger.info(f"Cleaned up clipped video: {analysis_video_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup clipped video: {e}")
        
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

class ExportRequest(BaseModel):
    media_id: str
    start: str  # HH:MM:SS.mmm format
    end: str    # HH:MM:SS.mmm format
    label: Optional[str] = None
    format: str = "mp4"

class ExportResponse(BaseModel):
    url: str
    sha256: Optional[str] = None
    start: str
    end: str
    label: Optional[str] = None
    size_bytes: int

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

# URL Ingestion Models
class UrlIngestRequest(BaseModel):
    url: str
    start: Optional[str] = None  # HH:MM:SS format
    end: Optional[str] = None    # HH:MM:SS format
    rights_confirmed: bool
    format_id: Optional[str] = None  # Specific format ID from /ingest/url/formats
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "start": "00:01:00",
                "end": "00:03:00",
                "rights_confirmed": True,
                "format_id": "137+140"
            }
        }

class UrlIngestResponse(BaseModel):
    media_id: str
    title: str
    duration: float  # seconds
    original_url: str  # local file URL
    window: Dict[str, Any]  # start, end, offsetSeconds
    format_used: Optional[str] = None  # format ID used for download
    codec_info: Optional[Dict[str, str]] = None  # vcodec, acodec info
    
    class Config:
        json_schema_extra = {
            "example": {
                "media_id": "yt_dQw4w9WgXcQ_1694567890",
                "title": "Rick Astley - Never Gonna Give You Up",
                "duration": 120.0,
                "original_url": "http://127.0.0.1:8000/uploads/url_tmp/yt_dQw4w9WgXcQ_1694567890.mp4",
                "window": {
                    "start": "00:01:00",
                    "end": "00:03:00",
                    "offsetSeconds": 60.0
                },
                "format_used": "137+140",
                "codec_info": {
                    "vcodec": "avc1.4d401f",
                    "acodec": "mp4a.40.2"
                }
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

@app.post("/export", tags=["Export"])
async def export_video_segment(request: ExportRequest):
    """
    Export a video segment as a downloadable MP4 clip.
    
    Args:
        request: ExportRequest with media_id, start/end times, optional label and format
        
    Returns:
        ExportResponse with download URL, SHA-256 hash, and metadata
    """
    logger.info(f"Export request: media_id={request.media_id}, start={request.start}, end={request.end}, label={request.label}")
    
    try:
        # Load configuration
        cfg = load_clip_config()
        export_config = cfg.get("export", {})
        export_enabled = export_config.get("enabled", True)
        
        if not export_enabled:
            raise HTTPException(status_code=503, detail="Export functionality is disabled")
        
        # Check FFmpeg availability
        if not has_ffmpeg():
            raise HTTPException(status_code=503, detail="FFmpeg not available for video export")
        
        # Resolve source path from media_id
        # Check both regular uploads and URL temp directory
        source_path = None
        
        # First, check if it's a URL-ingested media (starts with "yt_")
        if request.media_id.startswith("yt_"):
            url_tmp_path = os.path.join(URL_TMP_DIR, f"{request.media_id}.mp4")
            if os.path.exists(url_tmp_path):
                source_path = url_tmp_path
                logger.info(f"Found URL-ingested video: {source_path}")
        
        # If not found in URL temp, check regular uploads directory
        if not source_path:
            upload_dir = "content/uploads"
            if os.path.exists(upload_dir):
                # Find the actual video file by looking for files that start with the media_id
                video_files = []
                for filename in os.listdir(upload_dir):
                    if filename.startswith(request.media_id) and filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')):
                        video_files.append(filename)
                
                if video_files:
                    source_path = os.path.join(upload_dir, video_files[0])
                    logger.info(f"Found uploaded video: {source_path}")
        
        if not source_path:
            raise HTTPException(status_code=404, detail=f"No video file found for media_id: {request.media_id}")
        
        # Validate times using ffprobe
        video_info = get_video_info(source_path)
        if not video_info:
            raise HTTPException(status_code=400, detail="Could not read video information")
        
        # Extract duration from FFprobe output (nested in format section)
        video_duration = float(video_info.get("format", {}).get("duration", 0))
        logger.info(f"Video duration: {video_duration:.2f}s")
        
        # Parse start and end times
        from utils.time_utils import parse_hms_to_seconds
        try:
            start_seconds = parse_hms_to_seconds(request.start)
            end_seconds = parse_hms_to_seconds(request.end)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid time format: {e}")
        
        # Validate time window
        if start_seconds < 0 or end_seconds <= start_seconds or end_seconds > video_duration:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid time window: start={start_seconds:.2f}s, end={end_seconds:.2f}s, duration={video_duration:.2f}s"
            )
        
        # Build output path
        export_dir = os.path.join("results", "exports", request.media_id)
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate output filename
        start_clean = request.start.replace(":", "_").replace(".", "_")
        end_clean = request.end.replace(":", "_").replace(".", "_")
        label_suffix = f"_{request.label}" if request.label else ""
        output_filename = f"export_{start_clean}_to_{end_clean}{label_suffix}.mp4"
        output_path = os.path.join(export_dir, output_filename)
        
        # Build FFmpeg command for browser-safe MP4
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_seconds),
            "-to", str(end_seconds),
            "-i", source_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-movflags", "+faststart"
        ]
        
        # Add watermark if enabled
        watermark_enabled = export_config.get("watermark", True)
        if watermark_enabled:
            # Create watermark text with project info and UTC times
            # Escape colons in timestamps to prevent FFmpeg parsing issues
            start_escaped = request.start.replace(":", "\\:")
            end_escaped = request.end.replace(":", "\\:")
            watermark_text = f"Surveillance AI | {start_escaped}-{end_escaped} UTC"
            ffmpeg_cmd.extend([
                "-vf", f"drawtext=text='{watermark_text}':fontsize=12:fontcolor=white:x=10:y=10:box=1:boxcolor=black@0.5"
            ])
        
        ffmpeg_cmd.append(output_path)
        
        # Execute FFmpeg command
        import subprocess
        logger.info(f"Executing FFmpeg: {' '.join(ffmpeg_cmd)}")
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Video export failed: {result.stderr}")
        
        # Get file size
        file_size = os.path.getsize(output_path)
        
        # Compute SHA-256 if enabled
        sha256_hash = None
        hash_enabled = export_config.get("hash_sha256", True)
        if hash_enabled:
            with open(output_path, "rb") as f:
                sha256_hash = hashlib.sha256(f.read()).hexdigest()
            logger.info(f"SHA-256: {sha256_hash}")
        
        # Generate public URL
        store_type = export_config.get("store", "local")
        if store_type == "local":
            public_base_url = export_config.get("public_base_url", "http://127.0.0.1:8000")
            # Convert to web-accessible path
            relative_path = output_path.replace("\\", "/")
            public_url = f"{public_base_url}/{relative_path}"
        else:
            # TODO: Implement S3/GCS upload
            raise HTTPException(status_code=501, detail="S3/GCS export not yet implemented")
        
        logger.info(f"Export completed: {public_url} ({file_size} bytes)")
        
        return ExportResponse(
            url=public_url,
            sha256=sha256_hash,
            start=request.start,
            end=request.end,
            label=request.label,
            size_bytes=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

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
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
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
    # Load and validate URL ingestion config
    try:
        config = load_clip_config()
        url_config = config.get("url_ingest", {})
        if url_config.get("enabled", False):
            logger.info("URL ingestion enabled - YouTube URL analysis available")
            logger.info(f"URL work directory: {URL_TMP_DIR}")
            logger.info(f"Max duration: {url_config.get('max_duration_minutes', 120)} minutes")
            logger.info(f"Max size: {url_config.get('max_size_mb', 2048)} MB")
        else:
            logger.info("URL ingestion disabled - set url_ingest.enabled=true to enable")
    except Exception as e:
        logger.warning(f"Could not load URL ingestion config: {e}")
    
    # Start cleanup task
    asyncio.create_task(cleanup_task())

async def cleanup_task():
    """Periodic cleanup of old exports, URL temp files, and provenance records."""
    while True:
        try:
            current_time = datetime.now()
            
            # Clean up old exports
            to_delete = []
            for export_id, export in export_storage.items():
                created_at = datetime.fromisoformat(export.get("created_at", ""))
                if (current_time - created_at).total_seconds() > 3600:  # 1 hour
                    to_delete.append(export_id)
            
            for export_id in to_delete:
                del export_storage[export_id]
                logger.info(f"Cleaned up old export: {export_id}")
            
            # Clean up URL temp files and provenance records
            try:
                config = load_clip_config()
                url_config = config.get("url_ingest", {})
                keep_hours = url_config.get("keep_hours", 24)
                
                if url_config.get("enabled", False):
                    # Get old provenance records
                    old_records = provenance_db.get_old_records(keep_hours)
                    
                    for record in old_records:
                        # Delete the temp file if it exists
                        if os.path.exists(record.local_path):
                            try:
                                os.remove(record.local_path)
                                logger.info(f"Cleaned up URL temp file: {record.local_path}")
                            except Exception as e:
                                logger.warning(f"Could not delete temp file {record.local_path}: {e}")
                        
                        # Delete the provenance record
                        provenance_db.delete_record(record.media_id)
                        logger.info(f"Cleaned up provenance record: {record.media_id}")
                    
                    if old_records:
                        logger.info(f"Cleaned up {len(old_records)} old URL temp files and provenance records")
                        
            except Exception as e:
                logger.warning(f"URL cleanup error: {e}")
            
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
        
        await asyncio.sleep(300)  # Run every 5 minutes

class AnalyzeRequest(BaseModel):
    video_path: str
    prompts: List[str]
    model: Optional[str] = "clip"

class AnalyzeJsonWindow(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    offsetSeconds: Optional[float] = None

class AnalyzeJsonRequest(BaseModel):
    media_id: str
    prompts: List[str]
    model: Optional[str] = "clip"
    analysisWindow: Optional[AnalyzeJsonWindow] = None

# --- URL Ingestion helper functions ---
def parse_hms_to_seconds(hms_string: str) -> float:
    """Parse HH:MM:SS format to seconds."""
    try:
        parts = hms_string.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            return float(parts[0])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid time format: {hms_string}. Use HH:MM:SS or MM:SS or SS")

def build_ytdlp_command(url: str, output_path: str, start_seconds: float, end_seconds: Optional[float], 
                       format_id: Optional[str], config: Dict[str, Any]) -> List[str]:
    """Build yt-dlp command for downloading video segment."""
    cmd = ["yt-dlp"]
    
    # User agent
    user_agent = config.get("user_agent", "Mozilla/5.0")
    cmd.extend(["--user-agent", user_agent])
    
    # Format selection
    if format_id:
        # Use specific format ID from formats endpoint
        if "+" in format_id:
            # Video+Audio merge format (e.g., "137+140")
            cmd.extend(["-f", format_id])
        else:
            # Single format ID
            cmd.extend(["-f", format_id])
    else:
        # Auto selection - prefer H.264/AAC MP4 formats
        preferred_container = config.get("preferred_container", "mp4")
        prefer_codecs = config.get("prefer_codecs", ["h264", "avc1", "mp4a"])
        
        # Build format selector based on preferences
        format_selector = f"best[height>=720][ext={preferred_container}][fps>=30]/best[height>=480][ext={preferred_container}]/best[ext={preferred_container}]/best"
        cmd.extend(["-f", format_selector])
    
    cmd.extend(["--merge-output-format", "mp4"])
    
    # Time window (download only the requested segment)
    if start_seconds > 0 or end_seconds is not None:
        if end_seconds is not None:
            cmd.extend(["--download-sections", f"*{start_seconds}-{end_seconds}"])
        else:
            cmd.extend(["--download-sections", f"*{start_seconds}-"])
    
    # Output path
    cmd.extend(["-o", output_path])
    
    # Additional options for better compatibility
    # IMPORTANT: Do not pass boolean values to yt-dlp options like
    # --write-info-json/--write-thumbnail. Supplying "false" is
    # interpreted as another URL, which leads to the error:
    # "Fixed output name but more than one file to download".
    # Simply omit those flags so yt-dlp doesn't write extra files.
    cmd.extend([
        "--no-playlist",          # Don't download playlists
        "--no-check-certificate", # Skip SSL verification if needed
    ])
    
    # Add URL
    cmd.append(url)
    
    return cmd

def extract_video_title(stdout: str) -> Optional[str]:
    """Extract video title from yt-dlp output."""
    try:
        # Look for title in the output
        lines = stdout.split('\n')
        for line in lines:
            if '[download]' in line and 'Destination:' in line:
                # Extract filename and use it as title
                filename = line.split('Destination:')[-1].strip()
                title = os.path.splitext(os.path.basename(filename))[0]
                return title.replace('_', ' ').replace('-', ' ')
        return None
    except Exception:
        return None

def extract_channel_name(stdout: str) -> Optional[str]:
    """Extract channel name from yt-dlp output."""
    try:
        # Look for channel info in the output
        lines = stdout.split('\n')
        for line in lines:
            if 'uploader' in line.lower() or 'channel' in line.lower():
                # Extract channel name
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[-1].strip()
        return None
    except Exception:
        return None

# --- URL Ingestion endpoints ---
@app.post("/ingest/url", tags=["Ingest"])
async def ingest_youtube_url(request: UrlIngestRequest):
    """
    Ingest a YouTube URL by downloading only the requested time window.
    
    This endpoint fetches a specific time segment from a YouTube video and stores it
    as a temporary local file that can be analyzed using the standard /analyze endpoint.
    
    Args:
        request: URL ingestion request with YouTube URL, time window, and quality preferences
        
    Returns:
        UrlIngestResponse with media_id and local file URL for analysis
        
    Raises:
        403: URL ingestion is disabled in configuration
        400: Invalid URL, missing rights confirmation, or invalid time window
        413: Video exceeds size or duration limits
        500: Download or processing error
    """
    try:
        # Check if URL ingestion is enabled
        config = load_clip_config()
        url_config = config.get("url_ingest", {})
        
        if not url_config.get("enabled", False):
            raise HTTPException(
                status_code=403, 
                detail="URL ingestion is disabled. Set url_ingest.enabled=true in configuration to enable."
            )
        
        # Validate rights confirmation
        if not request.rights_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Rights confirmation required. You must confirm you have rights to download and analyze this content."
            )
        
        # Validate YouTube URL
        youtube_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_pattern, request.url)
        if not match:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL. Please provide a valid YouTube video URL."
            )
        
        video_id = match.group(1)
        logger.info(f"Processing YouTube video: {video_id}")
        
        # Parse time window
        start_seconds = 0.0
        end_seconds = None
        
        if request.start:
            try:
                start_seconds = parse_hms_to_seconds(request.start)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid start time format: {e}")
        
        if request.end:
            try:
                end_seconds = parse_hms_to_seconds(request.end)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid end time format: {e}")
        
        # Generate media_id
        epoch_time = int(time.time())
        media_id = f"yt_{video_id}_{epoch_time}"
        temp_output_path = os.path.join(URL_TMP_DIR, f"{media_id}_temp.mp4")
        final_output_path = os.path.join(URL_TMP_DIR, f"{media_id}.mp4")
        
        # Determine format to use
        format_to_use = request.format_id
        if not format_to_use:
            # Auto mode - select best format
            format_to_use = select_best_auto_format(request.url, url_config)
            logger.info(f"Auto-selected format: {format_to_use}")
        
        # Build yt-dlp command
        ytdlp_cmd = build_ytdlp_command(
            request.url, 
            temp_output_path, 
            start_seconds, 
            end_seconds, 
            format_to_use,
            url_config
        )
        
        logger.info(f"Executing yt-dlp command: {' '.join(ytdlp_cmd)}")
        logger.info(f"Using format: {format_to_use or 'auto'}")
        
        # Execute yt-dlp
        result = subprocess.run(
            ytdlp_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"yt-dlp failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download video: {result.stderr}"
            )
        
        # Check if file was created
        if not os.path.exists(temp_output_path):
            raise HTTPException(
                status_code=500,
                detail="Download completed but output file not found"
            )
        
        # Ensure browser-safe MP4 output
        logger.info(f"Ensuring browser-safe MP4: {temp_output_path} -> {final_output_path}")
        codec_info = ensure_browser_safe_mp4(temp_output_path, final_output_path)
        
        # Clean up temp file
        if os.path.exists(temp_output_path) and temp_output_path != final_output_path:
            os.remove(temp_output_path)
        
        # Use final output path for further processing
        output_path = final_output_path
        
        # Get file size and duration
        file_size_bytes = os.path.getsize(output_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Probe video duration
        video_info = get_video_info(output_path)
        duration_seconds = float(video_info.get("format", {}).get("duration", 0))
        duration_minutes = duration_seconds / 60
        
        # Check size and duration limits
        max_size_mb = url_config.get("max_size_mb", 2048)
        max_duration_minutes = url_config.get("max_duration_minutes", 120)
        
        if file_size_mb > max_size_mb:
            os.remove(output_path)
            raise HTTPException(
                status_code=413,
                detail=f"Video size ({file_size_mb:.1f} MB) exceeds limit ({max_size_mb} MB)"
            )
        
        if duration_minutes > max_duration_minutes:
            os.remove(output_path)
            raise HTTPException(
                status_code=413,
                detail=f"Video duration ({duration_minutes:.1f} minutes) exceeds limit ({max_duration_minutes} minutes)"
            )
        
        # Get video metadata from yt-dlp output
        title = extract_video_title(result.stdout) or f"YouTube Video {video_id}"
        channel = extract_channel_name(result.stdout) or "Unknown Channel"
        
        # Create provenance record
        provenance_record = create_provenance_record(
            media_id=media_id,
            source_url=request.url,
            provider="youtube",
            title=title,
            channel=channel,
            duration_s=duration_seconds,
            window_start_s=start_seconds,
            window_end_s=end_seconds or duration_seconds,
            local_path=output_path,
            file_size_bytes=file_size_bytes
        )
        
        # Save provenance record
        provenance_db.add_record(provenance_record)
        
        # Build response
        public_url = f"http://127.0.0.1:8000/uploads/url_tmp/{media_id}.mp4"
        
        response = UrlIngestResponse(
            media_id=media_id,
            title=title,
            duration=duration_seconds,
            original_url=public_url,
            window={
                "start": request.start or "00:00:00",
                "end": request.end or seconds_to_hms(duration_seconds),
                "offsetSeconds": start_seconds
            },
            format_used=format_to_use,
            codec_info=codec_info
        )
        
        logger.info(f"Successfully ingested YouTube URL: {media_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL ingestion error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def process_youtube_formats(formats: List[Dict[str, Any]], url_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process YouTube formats with merge detection and browser safety annotations.
    
    Args:
        formats: Raw format list from yt-dlp
        url_config: URL ingestion configuration
        
    Returns:
        Processed format list with merge detection and browser safety info
    """
    preferred_container = url_config.get("preferred_container", "mp4")
    prefer_codecs = url_config.get("prefer_codecs", ["h264", "avc1", "mp4a"])
    allow_av1_vp9 = url_config.get("allow_av1_vp9", True)
    
    processed = []
    video_formats = {}
    audio_formats = {}
    
    # Separate video and audio formats
    for fmt in formats:
        format_id = fmt.get("format_id", "")
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        ext = fmt.get("ext", "")
        
        # Skip formats without proper codec info
        if vcodec == "none" and acodec == "none":
            continue
            
        # Video-only formats
        if vcodec != "none" and acodec == "none":
            video_formats[format_id] = fmt
        # Audio-only formats  
        elif vcodec == "none" and acodec != "none":
            audio_formats[format_id] = fmt
        # Combined formats (video + audio)
        elif vcodec != "none" and acodec != "none":
            processed.append(create_format_entry(fmt, "av", url_config))
    
    # Create merged video+audio combinations
    for v_id, v_fmt in video_formats.items():
        # Find best matching audio format
        best_audio = find_best_audio_match(v_fmt, audio_formats)
        
        if best_audio:
            # Create merged format entry
            merged_format = create_merged_format_entry(v_fmt, best_audio, f"{v_id}+{best_audio['format_id']}")
            processed.append(merged_format)
        else:
            # Video-only format
            processed.append(create_format_entry(v_fmt, "video-only", url_config))
    
    # Add standalone audio formats
    for a_id, a_fmt in audio_formats.items():
        processed.append(create_format_entry(a_fmt, "audio-only", url_config))
    
    # Sort by height (desc), then by codec preference
    def sort_key(fmt):
        height = fmt.get("height", 0)
        if height is None:
            height = 0
        vcodec = fmt.get("vcodec", "")
        
        # Codec preference score (higher = better)
        codec_score = 0
        for i, preferred in enumerate(prefer_codecs):
            if preferred.lower() in vcodec.lower():
                codec_score = len(prefer_codecs) - i
                break
        
        return (-height, -codec_score)
    
    processed.sort(key=sort_key)
    return processed

def create_format_entry(fmt: Dict[str, Any], note: str, url_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized format entry."""
    preferred_container = url_config.get("preferred_container", "mp4")
    prefer_codecs = url_config.get("prefer_codecs", ["h264", "avc1", "mp4a"])
    allow_av1_vp9 = url_config.get("allow_av1_vp9", True)
    
    vcodec = fmt.get("vcodec", "none")
    acodec = fmt.get("acodec", "none")
    ext = fmt.get("ext", "")
    height = fmt.get("height", 0) or 0
    fps = fmt.get("fps", 0) or 0
    filesize = fmt.get("filesize", 0) or 0
    
    # Determine browser safety
    is_recommended = False
    warning = None
    
    if ext == preferred_container:
        if any(pref.lower() in vcodec.lower() for pref in prefer_codecs):
            is_recommended = True
        elif not allow_av1_vp9 and ("av01" in vcodec.lower() or "vp9" in vcodec.lower()):
            warning = "May require re-encoding for browser compatibility"
    
    return {
        "format_id": fmt.get("format_id", ""),
        "vcodec": vcodec,
        "acodec": acodec,
        "ext": ext,
        "resolution": f"{fmt.get('width', 0)}x{height}" if height > 0 else "unknown",
        "height": height,
        "fps": fps,
        "filesize": filesize,
        "note": note,
        "recommended": is_recommended,
        "warning": warning
    }

def create_merged_format_entry(video_fmt: Dict[str, Any], audio_fmt: Dict[str, Any], format_id: str) -> Dict[str, Any]:
    """Create a merged video+audio format entry."""
    # Use video format as base, add audio info
    merged = video_fmt.copy()
    merged["format_id"] = format_id
    merged["acodec"] = audio_fmt.get("acodec", "none")
    merged["note"] = "av"
    
    # Combine file sizes if available
    video_size = video_fmt.get("filesize", 0)
    audio_size = audio_fmt.get("filesize", 0)
    if video_size and audio_size:
        merged["filesize"] = video_size + audio_size
    
    return create_format_entry(merged, "av", {})

def find_best_audio_match(video_fmt: Dict[str, Any], audio_formats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find the best matching audio format for a video format."""
    if not audio_formats:
        return None
    
    # Prefer AAC audio for MP4 containers
    preferred_audio = None
    fallback_audio = None
    
    for audio_fmt in audio_formats.values():
        acodec = audio_fmt.get("acodec", "")
        ext = audio_fmt.get("ext", "")
        
        if "mp4a" in acodec.lower() or "aac" in acodec.lower():
            if not preferred_audio:
                preferred_audio = audio_fmt
        elif not fallback_audio:
            fallback_audio = audio_fmt
    
    return preferred_audio or fallback_audio

def select_best_auto_format(url: str, url_config: Dict[str, Any]) -> Optional[str]:
    """Select the best format for auto mode using format inspection."""
    try:
        # Get available formats
        cmd = ["yt-dlp", "-j", "--no-download", url]
        user_agent = url_config.get("user_agent", "Mozilla/5.0")
        cmd.extend(["--user-agent", user_agent])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.warning(f"Failed to inspect formats for auto selection: {result.stderr}")
            return None
        
        video_info = json.loads(result.stdout)
        formats = video_info.get("formats", [])
        
        # Find best H.264/AAC MP4 format under size cap
        max_size_mb = url_config.get("max_size_mb", 2048)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        suitable_formats = []
        for fmt in formats:
            vcodec = fmt.get("vcodec", "none")
            acodec = fmt.get("acodec", "none")
            ext = fmt.get("ext", "")
            filesize = fmt.get("filesize", 0) or 0
            
            # Check if it's H.264/AAC MP4
            if (ext == "mp4" and 
                "avc1" in vcodec.lower() and 
                "mp4a" in acodec.lower() and
                (filesize == 0 or filesize < max_size_bytes)):
                suitable_formats.append(fmt)
        
        if suitable_formats:
            # Sort by height (desc) and return format ID
            best_format = max(suitable_formats, key=lambda x: x.get("height", 0) or 0)
            return best_format.get("format_id")
        
        return None
        
    except Exception as e:
        logger.warning(f"Error in auto format selection: {e}")
        return None

def ensure_browser_safe_mp4(input_path: str, output_path: str) -> Dict[str, str]:
    """Re-encode video to browser-safe MP4 if needed."""
    try:
        # Check if file is already browser-safe
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", input_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            probe_data = json.loads(result.stdout)
            streams = probe_data.get("streams", [])
            
            is_h264 = False
            is_aac = False
            vcodec = "unknown"
            acodec = "unknown"
            
            for stream in streams:
                if stream.get("codec_type") == "video":
                    vcodec = stream.get("codec_name", "unknown")
                    is_h264 = vcodec in ["h264", "avc1"]
                elif stream.get("codec_type") == "audio":
                    acodec = stream.get("codec_name", "unknown")
                    is_aac = acodec in ["aac", "mp4a"]
            
            # If already H.264/AAC MP4, just copy
            if is_h264 and is_aac and input_path.endswith('.mp4'):
                shutil.copy2(input_path, output_path)
                logger.info(f"File already browser-safe, copied: {output_path}")
                return {"vcodec": vcodec, "acodec": acodec}
        
        # Re-encode to browser-safe MP4
        logger.info(f"Re-encoding to browser-safe MP4: {input_path} -> {output_path}")
        encode_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "baseline",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-movflags", "+faststart",
            output_path
        ]
        
        result = subprocess.run(encode_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"FFmpeg re-encoding failed: {result.stderr}")
        
        logger.info(f"Successfully re-encoded to browser-safe MP4: {output_path}")
        return {"vcodec": "h264", "acodec": "aac"}
        
    except Exception as e:
        logger.error(f"Error ensuring browser-safe MP4: {e}")
        # Fallback: just copy the original file
        shutil.copy2(input_path, output_path)
        return {"vcodec": "unknown", "acodec": "unknown"}


# --- Media Registry initialization ---
init_registry()


# --- Media Fetch/Probe API ---
class MediaFetchRequest(BaseModel):
    source: str  # "youtube" for now
    url: str
    action: str  # "probe" | "fetch"
    format_id: Optional[str] = None


@app.post("/media/fetch", tags=["Media"])
async def media_fetch(request: MediaFetchRequest):
    """
    Probe or fetch media and cache it in a simple registry.

    - action: "probe" returns metadata, thumbnails, and available formats (no download)
    - action: "fetch" downloads or reuses cached file and returns media_id and file_url
    """
    try:
        if request.source.lower() != "youtube":
            raise HTTPException(status_code=400, detail="Only source=youtube is supported currently")

        # Validate URL
        youtube_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_pattern, request.url)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        cfg = load_clip_config()
        url_config = (cfg.get("url_ingest") or {}) if isinstance(cfg, dict) else {}
        user_agent = url_config.get("user_agent", "Mozilla/5.0")

        # Probe mode uses yt-dlp -j --no-download
        if request.action.lower() == "probe":
            cmd = ["yt-dlp", "-j", "--no-download", request.url, "--user-agent", user_agent]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if result.returncode != 0:
                stderr = result.stderr.strip()
                # Map common yt-dlp errors
                if "Sign in to confirm your age" in stderr or "age-restricted" in stderr:
                    raise HTTPException(status_code=403, detail="Age-restricted or requires login")
                if "This video is private" in stderr:
                    raise HTTPException(status_code=403, detail="Video is private")
                if "This video is DRM protected" in stderr or "is DRM protected" in stderr:
                    raise HTTPException(status_code=403, detail="DRM protected video not supported")
                raise HTTPException(status_code=500, detail=f"yt-dlp failed: {stderr}")

            try:
                info = json.loads(result.stdout)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Failed to parse video info")

            title = info.get("title") or "Untitled"
            channel = info.get("uploader") or info.get("channel") or "Unknown"
            duration_s = float(info.get("duration", 0) or 0)
            thumbs = []
            for t in (info.get("thumbnails") or []):
                url = t.get("url") or t.get("thumbnail")
                if url:
                    thumbs.append({
                        "url": url,
                        "w": t.get("width") or 0,
                        "h": t.get("height") or 0,
                    })

            formats_raw = info.get("formats", [])
            processed_formats = process_youtube_formats(formats_raw, url_config)

            return {
                "source": "youtube",
                "title": title,
                "channel": channel,
                "duration_s": duration_s,
                "thumbs": thumbs,
                "formats": [
                    {
                        "format_id": f.get("format_id"),
                        "label": f"{(f.get('height') or 'unknown')}p ({f.get('vcodec')}/{f.get('acodec')})",
                        "vcodec": f.get("vcodec"),
                        "acodec": f.get("acodec"),
                        "filesize_mb": round((f.get("filesize") or 0) / (1024*1024), 2),
                    }
                    for f in processed_formats
                ],
            }

        # Fetch mode (download or reuse)
        if request.action.lower() == "fetch":
            chosen_format = request.format_id or select_best_auto_format(request.url, url_config)
            media_id = make_media_id(request.url, chosen_format)

            # Check cache
            cached = registry_find_by_key(request.url, request.format_id)
            if cached:
                file_path = cached.get("local_path")
                if file_path and os.path.exists(file_path):
                    registry_touch(cached["media_id"])
                    return {
                        "media_id": cached["media_id"],
                        "already_cached": True,
                        "title": cached.get("title"),
                        "duration_s": cached.get("duration_s"),
                        "thumbnail_url": cached.get("thumbnail_url"),
                        "format_id": cached.get("format_id"),
                        "file_url": cached.get("file_url"),
                    }

            # Not cached: download
            temp_path = os.path.join(UPLOAD_DIR, f"{media_id}_temp.mp4")
            final_path = os.path.join(UPLOAD_DIR, f"{media_id}.mp4")

            # Build yt-dlp command for full video
            ytdlp_cmd = ["yt-dlp", "--user-agent", user_agent]
            if chosen_format:
                ytdlp_cmd.extend(["-f", chosen_format])
            else:
                preferred_container = url_config.get("preferred_container", "mp4")
                format_selector = f"best[ext={preferred_container}]/best"
                ytdlp_cmd.extend(["-f", format_selector])
            ytdlp_cmd.extend(["--merge-output-format", "mp4", "-o", temp_path, request.url])

            result = subprocess.run(ytdlp_cmd, capture_output=True, text=True, timeout=1200)
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "Sign in to confirm your age" in stderr or "age-restricted" in stderr:
                    raise HTTPException(status_code=403, detail="Age-restricted or requires login")
                if "This video is private" in stderr:
                    raise HTTPException(status_code=403, detail="Video is private")
                if "DRM" in stderr:
                    raise HTTPException(status_code=403, detail="DRM protected video not supported")
                raise HTTPException(status_code=500, detail=f"yt-dlp failed: {stderr}")

            if not os.path.exists(temp_path):
                raise HTTPException(status_code=500, detail="Download succeeded but file missing")

            codec_info = ensure_browser_safe_mp4(temp_path, final_path)
            if os.path.exists(temp_path) and temp_path != final_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            # Probe metadata via ffprobe and a quick yt-dlp -j for title/thumb
            video_info = get_video_info(final_path)
            duration_s = float((video_info.get("format") or {}).get("duration", 0) or 0)
            title = None
            channel = None
            thumb_url = None
            try:
                probe_cmd = ["yt-dlp", "-j", "--no-download", request.url, "--user-agent", user_agent]
                probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=45)
                if probe_res.returncode == 0:
                    info = json.loads(probe_res.stdout)
                    title = info.get("title")
                    channel = info.get("uploader") or info.get("channel")
                    thumbs = info.get("thumbnails") or []
                    if thumbs:
                        # pick the last (often highest-res)
                        last = thumbs[-1]
                        thumb_url = last.get("url") or last.get("thumbnail")
            except Exception:
                pass

            # Build public URL
            rel_path = os.path.relpath(final_path, UPLOAD_DIR).replace('\\', '/')
            file_url = f"http://127.0.0.1:8000/uploads/{rel_path}" if not rel_path.startswith('..') else None

            # Upsert registry
            record = {
                "media_id": media_id,
                "source": "youtube",
                "url": request.url,
                "format_id": chosen_format or "auto",
                "title": title or media_id,
                "channel": channel or "Unknown",
                "duration_s": duration_s,
                "vcodec": codec_info.get("vcodec"),
                "acodec": codec_info.get("acodec"),
                "local_path": final_path,
                "file_url": file_url,
                "thumbnail_url": thumb_url,
                "size_bytes": os.path.getsize(final_path) if os.path.exists(final_path) else 0,
            }
            upsert_media(record)

            # Eviction stub based on config cap
            try:
                cache_cfg = (cfg.get("cache") or {}) if isinstance(cfg, dict) else {}
                max_total_gb = float(cache_cfg.get("max_total_gb", 8))
                registry_evict_if_needed(max_total_gb)
            except Exception as _e:
                logger.warning(f"Cache eviction check failed: {_e}")

            return {
                "media_id": media_id,
                "already_cached": False,
                "title": record["title"],
                "duration_s": record["duration_s"],
                "thumbnail_url": record["thumbnail_url"],
                "format_id": record["format_id"],
                "file_url": record["file_url"],
            }

        raise HTTPException(status_code=400, detail="Invalid action. Use 'probe' or 'fetch'.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/media/fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingest/url/formats", tags=["Ingest"])
async def get_youtube_formats(url: str = Query(..., description="YouTube URL to inspect")):
    """
    Inspect available formats for a YouTube URL without downloading.
    
    This endpoint returns the available video/audio formats for a given YouTube URL,
    allowing the frontend to populate a dynamic quality selection dropdown.
    
    Args:
        url: YouTube URL to inspect
        
    Returns:
        List of available formats with metadata for quality selection
        
    Raises:
        403: URL ingestion is disabled in configuration
        400: Invalid YouTube URL
        500: yt-dlp inspection error
    """
    try:
        # Check if URL ingestion is enabled
        config = load_clip_config()
        url_config = config.get("url_ingest", {})
        
        if not url_config.get("enabled", False):
            raise HTTPException(
                status_code=403, 
                detail="URL ingestion is disabled. Set url_ingest.enabled=true in configuration to enable."
            )
        
        # Validate YouTube URL
        youtube_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_pattern, url)
        if not match:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube URL. Please provide a valid YouTube video URL."
            )
        
        video_id = match.group(1)
        logger.info(f"Inspecting formats for YouTube video: {video_id}")
        
        # Build yt-dlp command for format inspection
        cmd = ["yt-dlp", "-j", "--no-download", url]
        
        # Add user agent if configured
        user_agent = url_config.get("user_agent", "Mozilla/5.0")
        cmd.extend(["--user-agent", user_agent])
        
        logger.info(f"Executing format inspection: {' '.join(cmd)}")
        
        # Execute yt-dlp to get format information
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout for inspection
        )
        
        if result.returncode != 0:
            logger.error(f"yt-dlp format inspection failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to inspect video formats: {result.stderr}"
            )
        
        # Parse the JSON output
        try:
            video_info = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse yt-dlp JSON output: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse video information")
        
        # Extract and process formats
        formats = video_info.get("formats", [])
        if not formats:
            raise HTTPException(status_code=500, detail="No formats available for this video")
        
        # Process formats with merge detection and browser safety
        processed_formats = process_youtube_formats(formats, url_config)
        
        logger.info(f"Found {len(processed_formats)} available formats for video {video_id}")
        return {"formats": processed_formats}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Format inspection error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze", tags=["Analyze"])
async def analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    prompts: Optional[str] = Form(None),
    model: Optional[str] = Form("clip"),
    start_ts: Optional[str] = Form(None),
    end_ts: Optional[str] = Form(None)
):
    """
    Analyze uploaded video with given prompts (file upload API).
    Enhanced with comprehensive error handling and job tracking.
    """
    logger.info(f"Starting analysis request")
    content_type = request.headers.get("content-type", "")
    logger.info(f"Content-Type: {content_type}")
    
    try:
        # Branch: JSON body with media_id (no upload)
        if content_type.startswith("application/json"):
            body = await request.json()
            logger.info(f"JSON analyze body: {body}")
            try:
                parsed = AnalyzeJsonRequest(**body)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

            # Resolve path via registry or direct file lookup
            reg = registry_get_by_id(parsed.media_id)
            if reg and reg.get("local_path") and os.path.exists(reg["local_path"]):
                # Found in registry (URL uploads)
                registry_touch(parsed.media_id)
                video_id = parsed.media_id
                video_path = reg["local_path"]
            else:
                # Check if it's a direct file (manual uploads)
                direct_path = os.path.join(UPLOAD_DIR, f"{parsed.media_id}.mp4")
                if os.path.exists(direct_path):
                    video_id = parsed.media_id
                    video_path = direct_path
                else:
                    raise HTTPException(status_code=404, detail="media_id not found or file missing")
            prompt_list = [p.strip() for p in parsed.prompts if str(p).strip()]
            if not prompt_list:
                raise HTTPException(status_code=400, detail="At least one prompt is required")

            # Optional window
            req_window = parsed.analysisWindow
            start_ts_json = req_window.start if req_window else None
            end_ts_json = req_window.end if req_window else None

            task_storage[video_id] = {
                "status": "queued",
                "progress": 0,
                "etaSeconds": None,
                "created_at": datetime.now().isoformat(),
            }

            background_tasks.add_task(
                process_video_analysis,
                video_id=video_id,
                video_path=video_path,
                prompts=prompt_list,
                model=parsed.model or "clip",
                start_ts=start_ts_json,
                end_ts=end_ts_json,
            )

            # Enrich media info for response compatibility
            # Build original_url if under /uploads
            original_url = None
            try:
                if os.path.exists(video_path):
                    rel_path = os.path.relpath(video_path, UPLOAD_DIR)
                    if not rel_path.startswith('..'):
                        rel_posix = rel_path.replace('\\', '/')
                        original_url = f"http://127.0.0.1:8000/uploads/{rel_posix}"
            except Exception:
                original_url = None

            # Duration via ffprobe
            duration_s = 0.0
            try:
                info = get_video_info(video_path)
                duration_s = float((info.get("format") or {}).get("duration", 0) or 0)
            except Exception:
                pass

            # Echo analysisWindow
            echoed_win = None
            if req_window:
                echoed_win = {
                    "start": req_window.start,
                    "end": req_window.end,
                    "offsetSeconds": req_window.offsetSeconds or 0,
                }

            resp = {
                "status": "queued",
                "video_id": video_id,
                "message": "Analysis started in background",
                "media": {
                    "media_id": video_id,
                    "source": reg.get("source") if reg else None,
                    "original_url": original_url,
                    "duration_s": duration_s,
                },
            }
            if echoed_win:
                resp["analysisWindow"] = echoed_win
            logger.info(f"Analyze(JSON) queued: {resp}")
            return resp

        # Multipart branch (legacy upload)
        if not file or not file.filename:
            error_response = error_handler.handle_validation_error(
                Exception("No filename provided"), "filename", getattr(file, 'filename', None)
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
            model=model,
            start_ts=start_ts,
            end_ts=end_ts
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

# NEW: Analyze by media_id for URL-ingested or previously uploaded files
class AnalyzeByIdRequest(BaseModel):
    media_id: str
    prompts: List[str]
    model: Optional[str] = "clip"
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None

@app.post("/analyze/by-id", tags=["Analyze"])
async def analyze_by_id(request: AnalyzeByIdRequest, background_tasks: BackgroundTasks):
    """Analyze a stored video by its media_id without re-uploading the file."""
    try:
        # Resolve source path from media_id
        source_path = None

        if request.media_id.startswith("yt_"):
            url_tmp_path = os.path.join(URL_TMP_DIR, f"{request.media_id}.mp4")
            if os.path.exists(url_tmp_path):
                source_path = url_tmp_path

        if not source_path:
            # Fallback: look in uploads directory for files starting with media_id
            if os.path.exists(UPLOAD_DIR):
                for filename in os.listdir(UPLOAD_DIR):
                    if filename.startswith(request.media_id) and filename.lower().endswith((".mp4",".avi",".mov",".mkv",".wmv",".flv")):
                        source_path = os.path.join(UPLOAD_DIR, filename)
                        break

        if not source_path:
            raise HTTPException(status_code=404, detail=f"No video file found for media_id: {request.media_id}")

        # Validate prompts
        prompt_list = [p.strip() for p in request.prompts if str(p).strip()]
        if not prompt_list:
            raise HTTPException(status_code=400, detail="At least one prompt is required")

        # Create job id and queue background task
        video_id = request.media_id
        task_storage[video_id] = {
            "status": "queued",
            "progress": 0,
            "etaSeconds": None,
            "created_at": datetime.now().isoformat(),
        }

        background_tasks.add_task(
            process_video_analysis,
            video_id=video_id,
            video_path=source_path,
            prompts=prompt_list,
            model=request.model or "clip",
            start_ts=request.start_ts,
            end_ts=request.end_ts,
        )

        return {
            "status": "queued",
            "video_id": video_id,
            "message": "Analysis started in background",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"analyze_by_id failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/environment", tags=["Health"])
def get_environment():
    """Get environment information."""
    return colab_compat.get_environment_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
