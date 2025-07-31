# backend_v3/app.py
"""
FastAPI app exposing the analyzer pipeline as a REST API.
Enhanced with error handling and Colab compatibility.
"""
import os
import json
import shutil
import logging
import traceback
from uuid import uuid4
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Import our new modules
from error_handler import error_handler, ErrorType
from colab_compat import colab_compat
from analyzer import analyze_video  # Use the main analyzer for model routing
from google_engine import analyze_with_google  # Google Video Intelligence placeholder

# --- Initialize Colab compatibility ---
colab_compat.log_environment()

# --- Configurable paths using Colab compatibility ---
UPLOAD_DIR = colab_compat.get_uploads_dir()
RESULTS_DIR = colab_compat.get_results_dir()
PREVIEWS_DIR = os.path.join(RESULTS_DIR, "previews")
LOGS_DIR = colab_compat.get_logs_dir()

# --- Ensure required folders exist ---
for d in [UPLOAD_DIR, RESULTS_DIR, PREVIEWS_DIR, LOGS_DIR]:
    colab_compat.ensure_directory(d)

# --- Enhanced logging setup ---
log_file = os.path.join(LOGS_DIR, "server.log")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("analyzer_api")

# --- FastAPI app ---
app = FastAPI(title="Surveillance AI Analyzer API", version="v3")

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

# --- CORS (optional, for frontend integration) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "version": "v3",
        "environment": "colab" if colab_compat.is_colab() else "local",
        "device": startup_device
    }

class AnalyzeRequest(BaseModel):
    video_path: str
    prompts: List[str]
    model: Optional[str] = "clip"

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    prompts: str = Form(...),
    model: str = Form("clip")  # Default to "clip" if not provided
):
    """
    Analyze uploaded video with given prompts (file upload API).
    Enhanced with comprehensive error handling.
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
        
        # Run analysis based on model parameter with error handling
        try:
            if model.lower() == "clip":
                logger.info(f"Starting CLIP analysis...")
                results, json_path = await analyze_video(
                    video_path=upload_path, 
                    prompts=prompt_list, 
                    output_dir=RESULTS_DIR
                )
            elif model.lower() == "google":
                logger.info(f"Starting Google analysis...")
                results, json_path = await analyze_with_google(
                    video_path=upload_path, 
                    prompts=prompt_list, 
                    output_dir=RESULTS_DIR
                )
            else:
                error_response = error_handler.handle_validation_error(
                    Exception(f"Unsupported model: {model}"), "model", model
                )
                return JSONResponse(status_code=400, content=error_response)
                
        except Exception as e:
            if "clip" in str(e).lower() or "model" in str(e).lower():
                error_response = error_handler.handle_clip_model_error(e, model)
            elif "frame" in str(e).lower():
                error_response = error_handler.handle_frame_extraction_error(e, upload_path)
            elif "prompt" in str(e).lower():
                error_response = error_handler.handle_prompt_interpreter_error(e, prompt_list)
            else:
                error_response = error_handler.create_error_response(e, ErrorType.UNKNOWN, {
                    "model": model,
                    "video_path": upload_path,
                    "prompts": prompt_list
                })
            return JSONResponse(status_code=500, content=error_response)
        
        # Handle new result format with alert classification
        if isinstance(results, dict):
            # New format with alert summary
            detections = results.get("detections", [])
            alert_summary = results.get("alert_summary", {})
            video_id = results.get("video_id", video_id)
            analysis_timestamp = results.get("analysis_timestamp", "")
            
            logger.info(f"Analysis completed successfully")
            logger.info(f"   Detections: {len(detections)}")
            logger.info(f"   Video ID: {video_id}")
            
            return {
                "status": "success",
                "video_id": video_id,
                "results": detections,
                "alert_summary": alert_summary,
                "analysis_timestamp": analysis_timestamp,
                "json_path": json_path.replace("\\", "/")
            }
        elif isinstance(results, list):
            # Legacy format - just detections
            logger.info(f"Analysis completed successfully")
            logger.info(f"   Detections: {len(results)}")
            
            return {
                "status": "success",
                "video_id": video_id,
                "results": results,
                "json_path": json_path.replace("\\", "/")
            }
        else:
            error_response = error_handler.create_error_response(
                Exception("Unexpected results format"), 
                ErrorType.UNKNOWN, 
                {"results_type": type(results).__name__}
            )
            return JSONResponse(status_code=500, content=error_response)
            
    except Exception as e:
        # Catch any unexpected errors
        error_response = error_handler.create_error_response(e, ErrorType.UNKNOWN, {
            "endpoint": "/analyze",
            "file": file.filename if file else None
        })
        return JSONResponse(status_code=500, content=error_response)

# --- Preserve old form endpoint for testing ---
@app.post("/analyze_form")
async def analyze_form(
    file: UploadFile = File(...),
    prompts: str = Form(...)
):
    """
    Analyze uploaded video with given prompts (legacy form API).
    """
    # Reuse the main analyze function logic
    return await analyze(file=file, prompts=prompts, model="clip")

@app.get("/environment")
def get_environment():
    """Get environment information."""
    return colab_compat.get_environment_info()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
