#!/usr/bin/env python3
"""
Colab Compatibility Module for Surveillance AI Backend-v3
Handles path differences between local and Google Colab environments.
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class ColabCompatibility:
    """Handles Colab environment compatibility and path management."""
    
    def __init__(self):
        """Initialize Colab compatibility checker."""
        self.logger = logging.getLogger("colab_compat")
        self._setup_paths()
    
    def _detect_colab_mode(self) -> bool:
        """Detect if running in Colab environment."""
        # Check environment variable
        if os.getenv("COLAB_MODE", "").lower() == "true":
            return True
        
        # Check for Colab-specific paths
        if os.path.exists("/content"):
            return True
        
        # Check for Colab runtime
        try:
            import google.colab
            return True
        except ImportError:
            pass
        
        return False
    
    def _setup_paths(self):
        """Setup paths based on environment."""
        self.is_colab_mode = self._detect_colab_mode()
        
        if self.is_colab_mode:
            self.logger.info("Running in Colab mode")
            self._setup_colab_paths()
        else:
            self.logger.info("Running in local mode")
            self._setup_local_paths()
    
    def _setup_colab_paths(self):
        """Setup paths for Colab environment."""
        self.paths = {
            "results_dir": "/content/results",
            "uploads_dir": "/content/uploads", 
            "frames_dir": "/content/frames",
            "models_dir": "/content/models",
            "json_dir": "/content/results/json",
            "logs_dir": "/content/logs",
            "temp_dir": "/content/temp"
        }
        
        # Create Colab directories
        for path in self.paths.values():
            os.makedirs(path, exist_ok=True)
    
    def _setup_local_paths(self):
        """Setup paths for local environment."""
        self.paths = {
            "results_dir": "./results",
            "uploads_dir": "./content/uploads",
            "frames_dir": "./content/frames", 
            "models_dir": "./models",
            "json_dir": "./results/json",
            "logs_dir": "./logs",
            "temp_dir": "./temp"
        }
        
        # Create local directories
        for path in self.paths.values():
            os.makedirs(path, exist_ok=True)
    
    def get_path(self, path_type: str) -> str:
        """Get path for specific type."""
        return self.paths.get(path_type, "")
    
    def get_all_paths(self) -> Dict[str, str]:
        """Get all configured paths."""
        return self.paths.copy()
    
    def ensure_directory(self, path: str) -> bool:
        """Ensure directory exists, create if needed."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    def get_model_cache_dir(self) -> str:
        """Get model cache directory."""
        return self.get_path("models_dir")
    
    def get_results_dir(self) -> str:
        """Get results directory."""
        return self.get_path("results_dir")
    
    def get_uploads_dir(self) -> str:
        """Get uploads directory."""
        return self.get_path("uploads_dir")
    
    def get_frames_dir(self) -> str:
        """Get frames directory."""
        return self.get_path("frames_dir")
    
    def get_json_dir(self) -> str:
        """Get JSON output directory."""
        return self.get_path("json_dir")
    
    def get_logs_dir(self) -> str:
        """Get logs directory."""
        return self.get_path("logs_dir")
    
    def is_colab(self) -> bool:
        """Check if running in Colab mode."""
        return self.is_colab_mode
    
    def refresh(self):
        """Refresh the environment detection."""
        self._setup_paths()
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        return {
            "is_colab": self.is_colab_mode,
            "paths": self.paths,
            "cwd": os.getcwd(),
            "env_vars": {
                "COLAB_MODE": os.getenv("COLAB_MODE", "false"),
                "CUDA_VISIBLE_DEVICES": os.getenv("CUDA_VISIBLE_DEVICES", "not_set")
            }
        }
    
    def log_environment(self):
        """Log environment information."""
        info = self.get_environment_info()
        self.logger.info(f"Environment: {'Colab' if info['is_colab'] else 'Local'}")
        self.logger.info(f"Working directory: {info['cwd']}")
        self.logger.info(f"Paths: {info['paths']}")

# Global Colab compatibility instance
# Don't instantiate at module level to allow environment variable changes
_colab_compat_instance = None

def get_colab_compat():
    """Get the global Colab compatibility instance."""
    global _colab_compat_instance
    if _colab_compat_instance is None:
        _colab_compat_instance = ColabCompatibility()
    return _colab_compat_instance

# For backward compatibility
colab_compat = get_colab_compat() 