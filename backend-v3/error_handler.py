#!/usr/bin/env python3
"""
Error Handling Module for Surveillance AI Backend-v3
Provides standardized error handling, logging, and response formatting.
"""
import os
import sys
import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from enum import Enum

class ErrorType(Enum):
    """Standardized error types for consistent handling."""
    FILE_IO = "file_io_error"
    FRAME_EXTRACTION = "frame_extraction_error"
    CLIP_MODEL = "clip_model_error"
    PROMPT_INTERPRETER = "prompt_interpreter_error"
    VALIDATION = "validation_error"
    NETWORK = "network_error"
    TIMEOUT = "timeout_error"
    UNKNOWN = "unknown_error"

class ErrorHandler:
    """Centralized error handling with logging and response formatting."""
    
    def __init__(self, log_file: str = "logs/server.log"):
        """Initialize error handler with logging setup."""
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup detailed logging to file and console."""
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("error_handler")
    
    def log_error(self, error: Exception, error_type: ErrorType, context: Dict[str, Any] = None):
        """Log error with full stack trace and context."""
        error_msg = f"ERROR [{error_type.value}]: {str(error)}"
        if context:
            error_msg += f" | Context: {json.dumps(context, default=str)}"
        
        self.logger.error(error_msg)
        self.logger.error(f"Stack trace:\n{traceback.format_exc()}")
    
    def create_error_response(self, error: Exception, error_type: ErrorType, 
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized error response."""
        error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(error)) % 10000}"
        
        response = {
            "status": "error",
            "error_type": error_type.value,
            "error_id": error_id,
            "message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            response["context"] = context
        
        # Log the error
        self.log_error(error, error_type, context)
        
        return response
    
    def handle_file_io_error(self, error: Exception, file_path: str, operation: str) -> Dict[str, Any]:
        """Handle file I/O errors."""
        context = {
            "file_path": file_path,
            "operation": operation,
            "file_exists": os.path.exists(file_path) if file_path else False
        }
        return self.create_error_response(error, ErrorType.FILE_IO, context)
    
    def handle_frame_extraction_error(self, error: Exception, video_path: str, frame_count: int = None) -> Dict[str, Any]:
        """Handle frame extraction errors."""
        context = {
            "video_path": video_path,
            "frame_count": frame_count,
            "video_exists": os.path.exists(video_path) if video_path else False
        }
        return self.create_error_response(error, ErrorType.FRAME_EXTRACTION, context)
    
    def handle_clip_model_error(self, error: Exception, model_name: str = None) -> Dict[str, Any]:
        """Handle CLIP model errors."""
        context = {
            "model_name": model_name,
            "cuda_available": self._check_cuda_availability()
        }
        return self.create_error_response(error, ErrorType.CLIP_MODEL, context)
    
    def handle_prompt_interpreter_error(self, error: Exception, prompts: list = None) -> Dict[str, Any]:
        """Handle prompt interpreter errors."""
        context = {
            "prompts": prompts,
            "prompt_count": len(prompts) if prompts else 0
        }
        return self.create_error_response(error, ErrorType.PROMPT_INTERPRETER, context)
    
    def handle_validation_error(self, error: Exception, field: str = None, value: Any = None) -> Dict[str, Any]:
        """Handle validation errors."""
        context = {
            "field": field,
            "value": str(value) if value is not None else None
        }
        return self.create_error_response(error, ErrorType.VALIDATION, context)
    
    def _check_cuda_availability(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def validate_video_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate video file format and accessibility."""
        if not file_path:
            return False, "No file path provided"
        
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "File is empty"
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                return False, "File too large (>500MB)"
        except OSError as e:
            return False, f"Cannot access file: {e}"
        
        # Check file extension
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in valid_extensions:
            return False, f"Unsupported file format: {file_ext}"
        
        return True, "File is valid"
    
    def validate_prompts(self, prompts: list) -> Tuple[bool, str]:
        """Validate prompt list."""
        if not prompts:
            return False, "No prompts provided"
        
        if not isinstance(prompts, list):
            return False, "Prompts must be a list"
        
        if len(prompts) == 0:
            return False, "Empty prompt list"
        
        # Check for empty or invalid prompts
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, str):
                return False, f"Prompt {i} is not a string"
            if not prompt.strip():
                return False, f"Prompt {i} is empty"
            if len(prompt.strip()) > 100:
                return False, f"Prompt {i} too long (>100 chars)"
        
        return True, "Prompts are valid"

# Global error handler instance
error_handler = ErrorHandler() 