# backend_v3/app.py
"""
FastAPI app exposing the analyzer pipeline as a REST API.
"""
import os
import json
import shutil
import logging
from uuid import uuid4
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .analyzer_simple import analyze_video_simple

# --- Configurable paths ---
UPLOAD_DIR = os.path.join("content", "uploads")
RESULTS_DIR = os.path.join("results")
PREVIEWS_DIR = os.path.join(RESULTS_DIR, "previews")

# --- Ensure required folders exist ---
for d in [UPLOAD_DIR, RESULTS_DIR, PREVIEWS_DIR]:
    os.makedirs(d, exist_ok=True)

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger("analyzer_api")

# --- FastAPI app ---
app = FastAPI(title="Surveillance AI Analyzer API", version="v3")

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
    return {"status": "ok", "version": "v3"}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    prompts: str = Form(...)
):
    """
    Analyze uploaded video with given prompts.
    """
    # 1. Save uploaded file
    video_id = f"video_{uuid4().hex[:8]}"
    filename = f"{video_id}.mp4"
    upload_path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(upload_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
    logger.info(f"Received video: {filename} ({file.filename})")

    # 2. Parse and clean prompts
    prompt_list = [p.strip() for p in prompts.split(",") if p.strip()]
    if not prompt_list:
        logger.error("No valid prompts provided.")
        raise HTTPException(status_code=400, detail="No valid prompts provided.")
    logger.info(f"Prompts: {prompt_list}")

    # 3. Run analysis
    logger.info(f"Starting analysis for {filename}...")
    try:
        json_path = analyze_video_simple(
            video_path=upload_path,
            prompts=prompt_list,
            output_dir=RESULTS_DIR
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    logger.info(f"Analysis complete for {filename}.")

    # Load results from JSON file
    try:
        with open(json_path, 'r') as f:
            results = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load results from {json_path}: {e}")
        results = []

    # 4. Return response
    return {
        "status": "success",
        "video_id": video_id,
        "results": results,
        "json_path": json_path.replace("\\", "/")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
