# 🚀 Enhanced Surveillance AI Backend Documentation

## 📋 Overview

The Surveillance AI backend has been enhanced to support **dual-mode operation** for public safety and law enforcement applications:

1. **Manual Upload Analysis** (`/analyze-manual`) - For existing CCTV footage
2. **Live Feed Analysis** (`/analyze-live`) - For real-time CCTV streams

## 🎯 Core Features

### ✅ Alert Classification System
The backend automatically classifies and flags critical events in real-time:

```json
{
  "alerts": {
    "alert": true,
    "alert_level": "critical",
    "alert_events": [
      {
        "category": "security",
        "event": "weapon detected",
        "confidence": 0.91,
        "timestamp": 15.5,
        "duration": 2.3
      }
    ],
    "total_alert_events": 1
  }
}
```

### ✅ Critical Event Categories
- **Security**: weapon, firearm, gun, knife, fight, violence, assault, theft, robbery
- **Safety**: fire, smoke, explosion, accident, fall, injury, medical emergency
- **Crowd**: crowd, panic, stampede, mob, protest, riot, unrest
- **Traffic**: accident, crash, collision, speeding, reckless driving
- **Suspicious**: loitering, suspicious activity, unauthorized access, trespassing

## 🔧 API Endpoints

### 1. Manual Upload Analysis
**Endpoint**: `POST /api/v1/analyze-manual`

**Purpose**: Analyze uploaded video footage for specific surveillance prompts

**Parameters**:
- `video`: Video file upload
- `prompt`: Analysis prompt (e.g., "find a man in red shirt near a car")
- `model`: AI model to use ("chatgpt" or "gemini")

**Response Structure**:
```json
{
  "status": "success",
  "analysis_type": "manual_upload",
  "request": {
    "prompt": "find suspicious activity",
    "model_used": "chatgpt",
    "video_filename": "cctv_footage.mp4",
    "video_size_bytes": 1048576
  },
  "processing": {
    "total_time_seconds": 45.2,
    "video_processing_time": 38.1,
    "llm_processing_time": 7.1
  },
  "analysis": {
    "ai_answer": "Analysis results...",
    "video_metadata": {...},
    "detections": {
      "labels": [...],
      "objects": [...],
      "shots": [...],
      "explicit_content": [...]
    },
    "summary": {...},
    "confidence_thresholds": {...},
    "high_confidence_detections": {...}
  },
  "alerts": {
    "alert": true,
    "alert_level": "critical",
    "alert_events": [...],
    "total_alert_events": 2
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

### 2. Live Feed Analysis
**Endpoint**: `POST /api/v1/analyze-live`

**Purpose**: Analyze live CCTV streams for real-time monitoring

**Parameters**:
- `video`: Video file upload (stream segment)
- `prompt`: Analysis prompt
- `model`: AI model to use ("chatgpt" or "gemini")
- `stream_id`: Optional stream identifier

**Response Structure**: Same as manual upload, but with `analysis_type: "live_feed"` and `stream_id` field.

### 3. Legacy Analysis (Backward Compatibility)
**Endpoint**: `POST /api/v1/analyze`

**Purpose**: Legacy endpoint for general video analysis

**Response Structure**: Same as manual upload, but with `analysis_type: "legacy"`.

### 4. Health Check
**Endpoint**: `GET /api/v1/health/detailed`

**Purpose**: Comprehensive system health check

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "system": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 30.1,
    "disk_free_gb": 150.5
  },
  "api_keys": {
    "openai_available": true,
    "gemini_available": true,
    "google_credentials_available": true
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
```

## 🔄 Processing Pipeline

### 1. Video Processing
- **Google Video Intelligence API**: Labels, objects, shots, explicit content
- **Modular Design**: Easy to swap for local models (CLIP, YOLO)
- **Metadata Extraction**: FPS, resolution, duration, frame count

### 2. Alert Classification
- **Real-time Analysis**: Immediate flagging of critical events
- **Confidence Thresholds**: High confidence (0.8+) for alerts
- **Category Classification**: Security, safety, crowd, traffic, suspicious
- **Severity Levels**: Critical (security/safety) vs Warning (others)

### 3. Prompt Interpretation
- **LangChain Integration**: Natural language processing
- **Multi-model Support**: ChatGPT and Gemini
- **Context-aware**: Uses video analysis results for informed responses

## 🏗️ Architecture

### Modular Video Processing
```python
# Easy processor swapping
from video_processor import GoogleVideoProcessor, LocalModelProcessor, set_processor

# Use Google Video Intelligence (default)
processor = GoogleVideoProcessor()
set_processor(processor)

# Future: Switch to local models
# processor = LocalModelProcessor("clip")
# set_processor(processor)
```

### Alert Classification Logic
```python
CRITICAL_EVENTS = {
    "security": ["weapon", "firearm", "gun", "knife", "fight", "violence"],
    "safety": ["fire", "smoke", "explosion", "accident", "fall"],
    "crowd": ["crowd", "panic", "stampede", "mob", "protest"],
    "traffic": ["accident", "crash", "collision", "speeding"],
    "suspicious": ["loitering", "suspicious activity", "unauthorized access"]
}
```

## 🔐 Security Features

### API Key Management
- **Environment Variables**: All keys loaded from `.env` file
- **Secure Storage**: No keys in code or git history
- **Health Checks**: Verify key availability without exposure

### Logging & Monitoring
- **Critical Alerts**: Console logging for immediate attention
- **Analysis Logs**: Detailed logs for audit trails
- **Error Handling**: Comprehensive exception handling

## 🚀 Usage Examples

### Manual Upload Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-manual" \
  -F "video=@cctv_footage.mp4" \
  -F "prompt=find any suspicious activity or weapons" \
  -F "model=chatgpt"
```

### Live Feed Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-live" \
  -F "video=@stream_segment.mp4" \
  -F "prompt=detect any security threats" \
  -F "model=gemini" \
  -F "stream_id=camera_001"
```

### Health Check
```bash
curl "http://localhost:8000/api/v1/health/detailed"
```

## 🔮 Future Enhancements

### Local Model Integration
- **CLIP Model**: For custom object detection
- **YOLO Model**: For real-time object tracking
- **Custom Models**: Domain-specific surveillance models

### Real-time Streaming
- **WebSocket Support**: For live video streams
- **RTSP Integration**: Direct camera feed processing
- **WebRTC Support**: Browser-based streaming

### Advanced Analytics
- **Behavioral Analysis**: Pattern recognition
- **Predictive Alerts**: Anomaly detection
- **Multi-camera Correlation**: Cross-camera event linking

## 📊 Performance Metrics

### Processing Times
- **Video Processing**: 30-60 seconds (depending on video length)
- **LLM Processing**: 5-15 seconds
- **Total Response**: 35-75 seconds

### Alert Sensitivity
- **High Confidence**: 0.8+ (reliable alerts)
- **Medium Confidence**: 0.5-0.8 (review recommended)
- **Low Confidence**: <0.5 (likely false positives)

## 🛠️ Development Setup

### Environment Variables
```bash
# .env file
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Dependencies
```bash
pip install -r requirements.txt
```

### Running the Backend
```bash
python main.py
```

## 📝 Logging

### Alert Logging
```
🚨 ALERT DETECTED: CRITICAL - 2 events
  - security: weapon detected (confidence: 0.91) at 15.5s
  - safety: fire detected (confidence: 0.85) at 18.2s
```

### Analysis Logging
```
Processing manual upload: content/uploads/manual_20250127_103000_cctv.mp4
AI Answer: Analysis complete...
Processing time: 45.2 seconds
```

## 🔧 Configuration

### Alert Thresholds
- **Confidence Threshold**: 0.7 (configurable)
- **High Priority Categories**: security, safety
- **Warning Categories**: crowd, traffic, suspicious

### Processing Options
- **Timeout**: 3 minutes for video processing
- **File Size**: No limit (configurable)
- **Supported Formats**: MP4, AVI, MOV, etc.

---

**This enhanced backend provides a robust foundation for AI-powered surveillance systems, with real-time alerting, modular architecture, and comprehensive monitoring capabilities.** 