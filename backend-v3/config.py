# backend_v3/config.py

# Confidence thresholds for each detection type
CONFIDENCE_THRESHOLDS = {
    'people': 0.7,
    'colors': 0.6,
    'fire': 0.85,
    'weapons': 0.9,
    'vehicles': 0.8,
    'unusual_activity': 0.8,
}

# Preview clip duration in seconds
PREVIEW_CLIP_DURATION = 5

# Model cache directory (Google Drive path or local)
MODEL_CACHE_DIR = 'content/model_cache'

# Output directories
PREVIEW_CLIP_DIR = 'content/previews'
OUTPUT_JSON_DIR = 'content/logs'

# Other runtime options
USE_GPU = True 