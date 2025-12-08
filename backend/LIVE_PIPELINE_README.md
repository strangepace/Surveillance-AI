# Live Stream Processing Pipeline

## Overview

The Live Stream Processing Pipeline provides real-time video analysis capabilities for surveillance applications. It continuously reads frames from video sources (RTSP streams, video files, or cameras), runs CLIP-based detection, and emits alerts when detections are found.

## Architecture

The pipeline consists of three main components:

1. **LiveSource** (`live_source.py`): Frame ingestion
   - Reads frames from RTSP URLs, video files, or camera devices
   - Samples frames at a controlled rate (configurable FPS)
   - Outputs frames to a queue

2. **LiveDetector** (`live_detector.py`): Detection processing
   - Consumes frames from a queue
   - Runs CLIP-based semantic detection
   - Emits alerts when detections match configured prompts

3. **LivePipeline** (`live_pipeline.py`): Main orchestrator
   - Coordinates LiveSource and LiveDetector
   - Manages queues and callbacks
   - Provides unified API

## Configuration

Add to `config/clip_config.yaml`:

```yaml
live_stream:
  source: "/path/to/video.mp4"  # or "rtsp://..." or "0" for camera
  source_type: ""  # Optional: "rtsp", "file", "camera" (auto-detected if empty)
  target_fps: 1.0  # Target frames per second (1-2 FPS recommended for MVP)
  prompts: ["person", "car", "fire"]  # Detection prompts
  max_frame_queue_size: 100
  max_alert_queue_size: 1000
```

## Usage

### Basic Usage

```python
import asyncio
from live_pipeline import LivePipeline
from config_loader import load_clip_config

async def main():
    config = load_clip_config()
    
    pipeline = LivePipeline(
        source="content/uploads/test_video.mp4",
        prompts=["person", "car", "fire"],
        config=config,
        target_fps=1.0
    )
    
    # Add alert callback
    def on_alert(alert):
        print(f"Alert: {alert.labels} @ {alert.timestamp_seconds:.2f}s")
    
    pipeline.add_alert_callback(on_alert)
    
    # Start pipeline
    await pipeline.start()
    
    try:
        # Run for 30 seconds
        await asyncio.sleep(30)
    finally:
        pipeline.stop()

asyncio.run(main())
```

### Using Config File

```python
from live_pipeline import create_pipeline_from_config
from config_loader import load_clip_config

config = load_clip_config()
pipeline = await create_pipeline_from_config(config)
await pipeline.start()
```

### Getting Alerts

```python
# Method 1: Callback (recommended)
pipeline.add_alert_callback(lambda alert: print(alert))

# Method 2: Polling
alert = pipeline.get_alert(timeout=1.0)
if alert:
    print(f"Alert: {alert.labels}")
```

## Testing

Run the test script:

```bash
cd backend
python test_live_pipeline.py
```

Or test with config:

```bash
python test_live_pipeline.py --config
```

## Alert Structure

```python
@dataclass
class Alert:
    timestamp_seconds: float  # Relative timestamp in stream
    frame_number: int  # Frame number
    labels: List[str]  # Detected labels
    confidence: float  # Confidence score (0-1)
    category: Optional[str] = None  # Alert category
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
```

## Source Types

### RTSP Stream
```python
pipeline = LivePipeline(
    source="rtsp://username:password@camera-ip:554/stream",
    prompts=["person"]
)
```

### Video File
```python
pipeline = LivePipeline(
    source="content/uploads/video.mp4",
    prompts=["person"]
)
```

### Camera Device
```python
pipeline = LivePipeline(
    source="0",  # Camera index
    prompts=["person"]
)
```

## Performance Considerations

- **Target FPS**: Start with 1.0 FPS for MVP. Higher rates increase CPU/GPU usage.
- **Queue Sizes**: Adjust based on your system. Larger queues use more memory but handle bursts better.
- **Similarity Threshold**: Lower threshold = more detections but more false positives.

## Next Steps (Tasks 7 & 8)

- **Task 7**: WebSocket integration to broadcast alerts to frontend
- **Task 8**: Live buffer for storing alerts and enabling replay

## Notes

- The pipeline runs detection in a separate thread to avoid blocking
- Frames are copied to avoid reference issues
- The pipeline gracefully handles source disconnections
- Alerts are queued and can be consumed asynchronously

