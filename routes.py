from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
from datetime import datetime
import logging
from prompt_interpreter import interpret_prompt # Stays the same
from video_processor import process_video       # Stays the same
from logger import log_analysis

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form("chatgpt") # Default to chatgpt
):
    try:
        start_time = datetime.now()
        
        # Validate model selection
        if model not in ["chatgpt", "gemini"]:
            raise HTTPException(status_code=400, detail="Invalid model selection. Use 'chatgpt' or 'gemini'.")
        
        # Save uploaded video
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Ensure the filename is unique to avoid conflicts
        video_path = f"content/uploads/video_{timestamp}_{video.filename}"
        
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # 1. Process video with Google Video Intelligence to get analysis
        video_analysis = await process_video(video_path)
        
        # 2. Use the analysis results to interpret the prompt and get the final answer
        final_answer = await interpret_prompt(
            prompt=prompt, 
            video_analysis_results=video_analysis, 
            model=model
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 3. Prepare the final response
        response = {
            "status": "success",
            "model_used": model,
            "processing_time_seconds": round(processing_time, 2),
            "question": prompt,
            "answer": final_answer,
            "raw_detections": video_analysis # Optionally include raw detections
        }
        
        # Log the analysis
        await log_analysis(video_path, prompt, model, response)
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {e}"
        )