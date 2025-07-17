from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
import logging
from prompt_interpreter import interpret_prompt
from video_processor import process_video
from logger import log_analysis
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# Critical event keywords for alert classification
CRITICAL_EVENTS = {
    "security": ["weapon", "firearm", "gun", "knife", "fight", "violence", "assault", "theft", "robbery"],
    "safety": ["fire", "smoke", "explosion", "accident", "fall", "injury", "medical emergency"],
    "crowd": ["crowd", "panic", "stampede", "mob", "protest", "riot", "unrest"],
    "traffic": ["accident", "crash", "collision", "speeding", "reckless driving"],
    "suspicious": ["loitering", "suspicious activity", "unauthorized access", "trespassing"]
}

def classify_alert(labels: List[Dict], objects: List[Dict], prompt: str) -> Dict[str, Any]:
    """
    Classify if the detected events should trigger an alert.
    Returns alert classification with severity and details.
    """
    alert_events = []
    alert_level = "none"
    
    # Check all detected labels and objects
    all_detections = labels + objects
    
    for detection in all_detections:
        label = detection.get("label", "").lower()
        confidence = detection.get("confidence", 0)
        
        # Check against critical event keywords
        for category, keywords in CRITICAL_EVENTS.items():
            for keyword in keywords:
                if keyword in label and confidence > 0.7:  # High confidence threshold for alerts
                    alert_events.append({
                        "category": category,
                        "event": label,
                        "confidence": confidence,
                        "timestamp": detection.get("start_time", 0),
                        "duration": detection.get("duration", 0)
                    })
    
    # Determine alert level
    if len(alert_events) > 0:
        # Check for high-priority events
        high_priority = any(event["category"] in ["security", "safety"] for event in alert_events)
        alert_level = "critical" if high_priority else "warning"
    
    return {
        "alert": alert_level != "none",
        "alert_level": alert_level,
        "alert_events": alert_events,
        "total_alert_events": len(alert_events)
    }

@router.post("/analyze-manual")
async def analyze_manual_upload(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form("chatgpt")
):
    """
    Analyze uploaded video footage for specific surveillance prompts.
    Designed for manual upload of existing CCTV footage or video files.
    """
    try:
        start_time = datetime.now()
        
        # Validate model selection
        if model not in ["chatgpt", "gemini"]:
            raise HTTPException(status_code=400, detail="Invalid model selection. Use 'chatgpt' or 'gemini'.")
        
        # Validate file type
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video file.")
        
        # Save uploaded video
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_path = f"content/uploads/manual_{timestamp}_{video.filename}"
        
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        logger.info(f"Processing manual upload: {video_path} with prompt: {prompt} using model: {model}")
        
        # Process video with Google Video Intelligence
        video_analysis = await process_video(video_path)
        
        # Classify alerts
        alert_classification = classify_alert(
            video_analysis.get("labels", []),
            video_analysis.get("objects", []),
            prompt
        )
        
        # Interpret prompt with analysis results
        final_answer = await interpret_prompt(
            prompt=prompt, 
            video_analysis_results=video_analysis, 
            model=model
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare structured response
        response = {
            "status": "success",
            "analysis_type": "manual_upload",
            "request": {
                "prompt": prompt,
                "model_used": model,
                "video_filename": video.filename,
                "video_size_bytes": len(content)
            },
            "processing": {
                "total_time_seconds": round(processing_time, 2),
                "video_processing_time": round(video_analysis.get("summary", {}).get("processing_time_seconds", 0), 2),
                "llm_processing_time": round(processing_time - video_analysis.get("summary", {}).get("processing_time_seconds", 0), 2)
            },
            "analysis": {
                "ai_answer": final_answer,
                "video_metadata": video_analysis.get("metadata", {}),
                "detections": {
                    "labels": video_analysis.get("labels", []),
                    "objects": video_analysis.get("objects", []),
                    "shots": video_analysis.get("shots", []),
                    "explicit_content": video_analysis.get("explicit_content", [])
                },
                "summary": video_analysis.get("summary", {}),
                "confidence_thresholds": video_analysis.get("confidence_thresholds", {}),
                "high_confidence_detections": {
                    "labels": video_analysis.get("high_confidence_labels", []),
                    "objects": video_analysis.get("high_confidence_objects", [])
                }
            },
            "alerts": alert_classification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the analysis
        await log_analysis(video_path, prompt, model, response)
        
        # Log critical alerts to console
        if alert_classification["alert"]:
            logger.warning(f"🚨 ALERT DETECTED: {alert_classification['alert_level'].upper()} - {len(alert_classification['alert_events'])} events")
            for event in alert_classification["alert_events"]:
                logger.warning(f"  - {event['category']}: {event['event']} (confidence: {event['confidence']:.2f}) at {event['timestamp']:.1f}s")
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing manual upload: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Manual upload processing failed: {str(e)}"
        )

@router.post("/analyze-live")
async def analyze_live_feed(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form("chatgpt"),
    stream_id: Optional[str] = Form(None)
):
    """
    Analyze live CCTV stream for real-time surveillance monitoring.
    Designed for continuous monitoring with immediate alert classification.
    """
    try:
        start_time = datetime.now()
        
        # Validate model selection
        if model not in ["chatgpt", "gemini"]:
            raise HTTPException(status_code=400, detail="Invalid model selection. Use 'chatgpt' or 'gemini'.")
        
        # Validate file type
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video file.")
        
        # Save live stream segment
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        stream_id = stream_id or "live_stream"
        video_path = f"content/uploads/live_{stream_id}_{timestamp}_{video.filename}"
        
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        logger.info(f"Processing live feed: {video_path} with prompt: {prompt} using model: {model}")
        
        # Process video with Google Video Intelligence
        video_analysis = await process_video(video_path)
        
        # Classify alerts (more sensitive for live feeds)
        alert_classification = classify_alert(
            video_analysis.get("labels", []),
            video_analysis.get("objects", []),
            prompt
        )
        
        # For live feeds, we might want faster processing
        # Use a simplified prompt interpretation for real-time response
        final_answer = await interpret_prompt(
            prompt=prompt, 
            video_analysis_results=video_analysis, 
            model=model
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare structured response optimized for live monitoring
        response = {
            "status": "success",
            "analysis_type": "live_feed",
            "stream_id": stream_id,
            "request": {
                "prompt": prompt,
                "model_used": model,
                "video_filename": video.filename,
                "video_size_bytes": len(content)
            },
            "processing": {
                "total_time_seconds": round(processing_time, 2),
                "video_processing_time": round(video_analysis.get("summary", {}).get("processing_time_seconds", 0), 2),
                "llm_processing_time": round(processing_time - video_analysis.get("summary", {}).get("processing_time_seconds", 0), 2)
            },
            "analysis": {
                "ai_answer": final_answer,
                "video_metadata": video_analysis.get("metadata", {}),
                "detections": {
                    "labels": video_analysis.get("labels", []),
                    "objects": video_analysis.get("objects", []),
                    "shots": video_analysis.get("shots", []),
                    "explicit_content": video_analysis.get("explicit_content", [])
                },
                "summary": video_analysis.get("summary", {}),
                "confidence_thresholds": video_analysis.get("confidence_thresholds", {}),
                "high_confidence_detections": {
                    "labels": video_analysis.get("high_confidence_labels", []),
                    "objects": video_analysis.get("high_confidence_objects", [])
                }
            },
            "alerts": alert_classification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the analysis
        await log_analysis(video_path, prompt, model, response)
        
        # Log critical alerts to console with higher priority for live feeds
        if alert_classification["alert"]:
            logger.critical(f"🚨 LIVE ALERT DETECTED: {alert_classification['alert_level'].upper()} - {len(alert_classification['alert_events'])} events")
            for event in alert_classification["alert_events"]:
                logger.critical(f"  - {event['category']}: {event['event']} (confidence: {event['confidence']:.2f}) at {event['timestamp']:.1f}s")
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing live feed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Live feed processing failed: {str(e)}"
        )

# Keep the original /analyze endpoint for backward compatibility
@router.post("/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form("chatgpt")
):
    """
    Legacy endpoint for video analysis. Use /analyze-manual or /analyze-live for specific use cases.
    """
    try:
        start_time = datetime.now()
        
        # Validate model selection
        if model not in ["chatgpt", "gemini"]:
            raise HTTPException(status_code=400, detail="Invalid model selection. Use 'chatgpt' or 'gemini'.")
        
        # Validate file type
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video file.")
        
        # Save uploaded video
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_path = f"content/uploads/video_{timestamp}_{video.filename}"
        
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        logger.info(f"Processing video: {video_path} with prompt: {prompt} using model: {model}")
        
        # Process video with Google Video Intelligence
        video_analysis = await process_video(video_path)
        
        # Classify alerts
        alert_classification = classify_alert(
            video_analysis.get("labels", []),
            video_analysis.get("objects", []),
            prompt
        )
        
        # Interpret prompt with analysis results
        final_answer = await interpret_prompt(
            prompt=prompt, 
            video_analysis_results=video_analysis, 
            model=model
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare enhanced response
        response = {
            "status": "success",
            "analysis_type": "legacy",
            "request": {
                "prompt": prompt,
                "model_used": model,
                "video_filename": video.filename,
                "video_size_bytes": len(content)
            },
            "processing": {
                "total_time_seconds": round(processing_time, 2),
                "video_processing_time": round(video_analysis.get("summary", {}).get("processing_time_seconds", 0), 2),
                "llm_processing_time": round(processing_time - video_analysis.get("summary", {}).get("processing_time_seconds", 0), 2)
            },
            "analysis": {
                "ai_answer": final_answer,
                "video_metadata": video_analysis.get("metadata", {}),
                "detections": {
                    "labels": video_analysis.get("labels", []),
                    "objects": video_analysis.get("objects", []),
                    "shots": video_analysis.get("shots", []),
                    "explicit_content": video_analysis.get("explicit_content", [])
                },
                "summary": video_analysis.get("summary", {}),
                "confidence_thresholds": video_analysis.get("confidence_thresholds", {}),
                "high_confidence_detections": {
                    "labels": video_analysis.get("high_confidence_labels", []),
                    "objects": video_analysis.get("high_confidence_objects", [])
                }
            },
            "alerts": alert_classification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the analysis
        await log_analysis(video_path, prompt, model, response)
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(e)}"
        )

@router.get("/gcp-info")
async def gcp_info():
    """
    Temporary endpoint to verify Google credentials and project ID.
    """
    try:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
        info = {}
        if os.path.exists(cred_path):
            with open(cred_path, "r") as f:
                creds = json.load(f)
                info["project_id"] = creds.get("project_id")
                info["client_email"] = creds.get("client_email")
        else:
            info["error"] = f"Credentials file not found at {cred_path}"
        # Try a simple Video Intelligence API call
        try:
            from google.cloud import videointelligence_v1
            client = videointelligence_v1.VideoIntelligenceServiceClient()
            info["video_intelligence_client"] = "initialized"
        except Exception as e:
            info["video_intelligence_client_error"] = str(e)
        return info
    except Exception as e:
        return {"error": str(e)}

@router.get("/health/detailed")
async def detailed_health_check():
    """
    Enhanced health check endpoint with system information.
    """
    try:
        import psutil
        
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check API keys availability (without exposing them)
        openai_key_available = bool(os.getenv('OPENAI_API_KEY'))
        gemini_key_available = bool(os.getenv('GEMINI_API_KEY'))
        google_credentials_available = os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "api_keys": {
                "openai_available": openai_key_available,
                "gemini_available": gemini_key_available,
                "google_credentials_available": google_credentials_available
            },
            "services": {
                "video_processor": "available",
                "prompt_interpreter": "available",
                "logger": "available"
            },
            "endpoints": {
                "analyze_manual": "available",
                "analyze_live": "available",
                "analyze_legacy": "available"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")