import json
import os
import logging
from datetime import datetime
from typing import Dict, Any
import shutil

logger = logging.getLogger(__name__)

async def log_analysis(
    video_path: str,
    prompt: str,
    model: str,
    response: Dict[str, Any]
) -> None:
    """
    Log the analysis results to a JSON file.
    Implements log rotation if file size exceeds 5MB.
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("content/logs", exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"content/logs/analysis_{timestamp}.json"
        
        # Prepare log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "video_path": video_path,
            "prompt": prompt,
            "model": model,
            "response": response
        }
        
        # Write log entry
        with open(log_file, "w") as f:
            json.dump(log_entry, f, indent=2)
        
        # Check log rotation
        await rotate_logs()
        
    except Exception as e:
        logger.error(f"Error logging analysis: {str(e)}")
        # Don't raise the exception as logging failure shouldn't affect the main flow

async def rotate_logs() -> None:
    """
    Implement log rotation if total log size exceeds 5MB.
    Keeps only the most recent logs.
    """
    try:
        log_dir = "content/logs"
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        
        # Get all log files
        log_files = [f for f in os.listdir(log_dir) if f.startswith("analysis_")]
        
        # Calculate total size
        total_size = sum(os.path.getsize(os.path.join(log_dir, f)) for f in log_files)
        
        # If total size exceeds max_size, remove oldest logs
        if total_size > max_size:
            # Sort files by modification time (oldest first)
            log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
            
            # Remove oldest files until we're under the size limit
            for log_file in log_files:
                if total_size <= max_size:
                    break
                    
                file_path = os.path.join(log_dir, log_file)
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                total_size -= file_size
                
    except Exception as e:
        logger.error(f"Error rotating logs: {str(e)}")
        # Don't raise the exception as log rotation failure shouldn't affect the main flow 