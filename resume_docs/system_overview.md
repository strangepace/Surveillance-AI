# Surveillance AI Resume Docs - Chunk 1/6

## Question:
Explain in clear technical language how the entire Surveillance AI system is structured — backend, frontend, and their interconnections.

Include:
- Frameworks and APIs (FastAPI, LangChain, CLIP, Google Video Intelligence API, etc.)
- Data flow: video upload → analysis → result display
- All detection modes (FullScan, FrameSkip, MotionFilter, TrackThenMatch, ActivityDetection)
- Key functional flow between components (frontend ↔ backend)

## Answer:

### System Architecture Overview

The Surveillance AI system is a full-stack video analysis platform built with modern web technologies, featuring intelligent caching, YouTube integration, and real-time AI-powered object detection. The architecture follows a clean separation between frontend and backend, with robust API communication and intelligent media management.

### Core Technology Stack

**Backend Framework & APIs:**
- **FastAPI**: High-performance Python web framework providing RESTful APIs with automatic OpenAPI documentation
- **CLIP (Contrastive Language-Image Pre-training)**: OpenAI's multimodal AI model for semantic video analysis and object detection
- **yt-dlp**: Command-line tool for YouTube video extraction and format inspection
- **FFmpeg/FFprobe**: Multimedia framework for video processing, format conversion, and metadata extraction
- **Pydantic**: Data validation and settings management for API request/response models
- **SQLite/JSON**: Lightweight data storage for media registry and caching

**Frontend Technologies:**
- **React 18**: Modern JavaScript library for building dynamic user interfaces
- **TypeScript**: Type-safe JavaScript for enhanced development experience
- **Vite**: Fast build tool and development server
- **Context API**: Global state management for upload and analysis workflows
- **localStorage**: Client-side persistence for run history and user preferences

### System Architecture & Data Flow

#### 1. Video Ingestion Pipeline

**Manual Upload Flow:**
```
User selects file → Frontend validation → POST /analyze (multipart/form-data) 
→ Backend processes → CLIP analysis → Results stored → Frontend displays
```

**YouTube Integration Flow:**
```
URL paste → POST /media/fetch (probe) → Format inspection → User selects format 
→ POST /media/fetch (fetch) → Download/cache → POST /analyze (media_id) 
→ CLIP analysis → Results with caching metadata
```

#### 2. Backend Architecture

**Core Components:**
- **`app.py`**: Main FastAPI application with REST endpoints
- **`analyzer.py`**: CLIP model integration and video analysis engine
- **`media_registry.py`**: JSON-backed caching system for downloaded media
- **`clip_config.yaml`**: Configuration management for analysis parameters

**Key Endpoints:**
- `POST /analyze`: Core analysis endpoint supporting both file uploads and media_id references
- `POST /media/fetch`: YouTube integration with probe/fetch actions
- `GET /ingest/url/formats`: Dynamic format inspection for YouTube videos
- `GET /status/{job_id}`: Real-time analysis progress tracking
- `GET /results/{job_id}`: Retrieval of analysis results

#### 3. Frontend Architecture

**Component Structure:**
- **`Upload.tsx`**: Main upload interface with manual and URL tabs
- **`Results.tsx`**: Results display with re-analysis capabilities and run history
- **`UrlIngestForm.tsx`**: YouTube URL processing with format selection
- **`PromptChipsInput.tsx`**: Reusable prompt input component
- **`VideoRangeSelector.tsx`**: Time window selection for analysis

**State Management:**
- **`useUpload` Context**: Global state for upload progress, analysis results, and media metadata
- **Route State**: URL-based state management for job IDs and analysis parameters
- **localStorage**: Persistent storage for run history and user preferences

### Detection Modes & Analysis Engine

#### 1. FullScan Mode
- **Purpose**: Comprehensive frame-by-frame analysis
- **Implementation**: Processes every frame at specified intervals
- **Use Case**: Maximum detection accuracy for critical analysis
- **Performance**: Higher computational cost, longer processing time

#### 2. FrameSkip Mode
- **Purpose**: Optimized analysis with intelligent frame sampling
- **Implementation**: Analyzes frames at configurable intervals (e.g., every 5th frame)
- **Use Case**: Balanced accuracy and performance for large videos
- **Performance**: Reduced processing time while maintaining detection quality

#### 3. MotionFilter Mode
- **Purpose**: Motion-based frame selection for analysis
- **Implementation**: Uses optical flow or frame differencing to identify motion
- **Use Case**: Focus analysis on areas with activity, reducing false positives
- **Performance**: Efficient processing by skipping static scenes

#### 4. TrackThenMatch Mode
- **Purpose**: Object tracking followed by semantic matching
- **Implementation**: Tracks objects across frames, then applies CLIP analysis
- **Use Case**: Consistent object detection across video sequences
- **Performance**: Reduces redundant analysis of tracked objects

#### 5. ActivityDetection Mode
- **Purpose**: High-level activity recognition and classification
- **Implementation**: Combines motion detection with semantic analysis
- **Use Case**: Identifying specific activities or behaviors
- **Performance**: Optimized for activity-level insights rather than object detection

### Data Flow Architecture

#### 1. Upload & Processing Flow
```
User Input → Frontend Validation → Backend Processing → AI Analysis → Result Storage → Frontend Display
```

#### 2. YouTube Integration Flow
```
URL Input → Format Probe → User Selection → Download/Cache → Analysis → Results with Metadata
```

#### 3. Re-analysis Flow
```
Existing Media → New Prompts → Analysis (No Re-download) → Updated Results → History Tracking
```

### Key Functional Interconnections

#### Frontend ↔ Backend Communication
- **RESTful APIs**: Clean separation with JSON request/response patterns
- **Real-time Updates**: Polling-based status updates during analysis
- **Error Handling**: Comprehensive error states with user-friendly messages
- **Caching Strategy**: Intelligent media reuse to prevent redundant downloads

#### Media Management System
- **Registry-based Caching**: SHA1-hashed media IDs for efficient storage
- **Format Optimization**: Automatic conversion to browser-safe MP4/H.264
- **Size Management**: Configurable cache limits with LRU eviction
- **Metadata Tracking**: Comprehensive media information storage

#### Analysis Pipeline
- **CLIP Integration**: Semantic understanding of video content
- **Configurable Parameters**: Flexible analysis window and detection modes
- **Result Persistence**: Structured storage of analysis results
- **Progress Tracking**: Real-time status updates during processing

### Performance Optimizations

#### Backend Optimizations
- **Async Processing**: Non-blocking I/O for video analysis
- **Format Conversion**: Efficient FFmpeg-based video processing
- **Caching Strategy**: Intelligent media reuse and storage management
- **Error Recovery**: Robust handling of yt-dlp and FFmpeg failures

#### Frontend Optimizations
- **Component Lazy Loading**: Efficient rendering of large result sets
- **State Management**: Optimized re-renders and data flow
- **Caching**: Client-side result caching for fast navigation
- **UX Enhancements**: Loading states, error handling, and responsive design

### Security & Reliability

#### Data Security
- **Input Validation**: Comprehensive validation of user inputs and file uploads
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **File Safety**: Secure handling of uploaded and downloaded media

#### Error Handling
- **Graceful Degradation**: Fallback mechanisms for API failures
- **User Feedback**: Clear error messages and recovery options
- **Logging**: Comprehensive logging for debugging and monitoring

This architecture demonstrates advanced full-stack development skills, AI/ML integration, and modern software engineering practices, making it an excellent showcase project for technical resumes.
