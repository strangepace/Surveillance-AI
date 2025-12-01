# Surveillance AI Resume Docs - Chunk 2/6

## Question:
Document all backend components and logic for the Surveillance AI project.

Include:
- Main modules and classes (PeopleDetector, ColorDetector, FireDetector, VehicleDetector, etc.)
- Multi-label detection pipeline and prioritization logic
- CLIP + FAISS usage for embedding-based search
- Detection pipeline: input → preprocessing → inference → timestamp extraction → JSON output
- Adjustable confidence threshold implementation
- Dynamic model loading (YOLOv8, CLIP B/32) and Drive caching for Colab runtime

## Answer:

### Backend Architecture Overview

The Surveillance AI backend is a sophisticated video analysis system built on FastAPI, featuring modular detector classes, intelligent caching, and advanced AI model integration. The system processes video content through a comprehensive pipeline that extracts frames, applies semantic analysis, and generates structured detection results.

### Core Backend Modules & Classes

#### 1. Main Analyzer Pipeline (`analyzer.py`)

**VideoAnalyzer Class:**
- **Purpose**: Central orchestrator for video analysis pipeline
- **Key Features**:
  - CLIP model integration with dynamic loading
  - Configurable similarity thresholds (default: 0.21)
  - Error handling with comprehensive logging
  - Colab compatibility for cloud deployment
  - Frame extraction and preprocessing
  - Multi-prompt analysis support

**DetectionResult Dataclass:**
```python
@dataclass
class DetectionResult:
    timestamp: str
    labels: List[str]
    confidence: float
    preview_clip: str
    summary: Optional[str] = None
    frame_index: Optional[int] = None
    prompt_matches: Optional[List[str]] = None
```

#### 2. Specialized Detector Classes (`detectors.py`)

**PeopleDetector:**
- **Purpose**: Human detection, age/gender classification, clothing analysis
- **Implementation**: CLIP-based semantic understanding
- **Features**: Multi-prompt scoring, confidence-based filtering
- **Use Cases**: Security monitoring, demographic analysis, behavior tracking

**ColorDetector:**
- **Purpose**: Color-based object detection and classification
- **Implementation**: CLIP model with color-specific prompts
- **Features**: RGB analysis, color similarity matching
- **Use Cases**: Vehicle tracking, object identification, scene analysis

**FireDetector:**
- **Purpose**: Fire, flame, and smoke detection
- **Implementation**: Specialized fire detection prompts
- **Features**: High-confidence threshold (0.85), safety-critical analysis
- **Use Cases**: Fire safety monitoring, emergency detection

**VehicleDetector (Planned):**
- **Purpose**: Vehicle detection and classification
- **Implementation**: YOLOv8 + CLIP hybrid approach
- **Features**: Real-time vehicle tracking, type classification
- **Use Cases**: Traffic monitoring, parking management

**WeaponsDetector (Planned):**
- **Purpose**: Weapon and dangerous object detection
- **Implementation**: High-confidence threshold (0.9)
- **Features**: Security-focused analysis, alert generation
- **Use Cases**: Security screening, threat detection

#### 3. Detection Engine (`engine.py`)

**DetectionEngine Class:**
- **Purpose**: Orchestrates multiple detector classes
- **Features**:
  - Multi-detector aggregation
  - Result deduplication and merging
  - Preview clip generation
  - Confidence-based filtering
- **Pipeline**: Video input → Multi-detector analysis → Result aggregation → JSON output

#### 4. Alert Classification System (`alert_classifier.py`)

**AlertClassifier Class:**
- **Purpose**: Categorizes detections into alert priorities
- **Categories**:
  - **Security**: Weapons, suspicious behavior (Priority: High)
  - **Safety**: Fire, accidents, hazards (Priority: High)
  - **Operational**: People counting, vehicle tracking (Priority: Medium)
  - **General**: Miscellaneous detections (Priority: Low)
- **Features**: Keyword matching, priority assignment, alert summarization

### Multi-Label Detection Pipeline

#### 1. Input Processing
```
Video Input → Frame Extraction → Preprocessing → Multi-Detector Analysis
```

#### 2. Detection Pipeline Flow
```
Raw Video → Frame Sampling → CLIP Encoding → Prompt Matching → Confidence Scoring → Threshold Filtering → Result Aggregation
```

#### 3. Prioritization Logic
- **High Priority**: Security threats, safety hazards (confidence ≥ 0.85)
- **Medium Priority**: Operational detections (confidence ≥ 0.7)
- **Low Priority**: General detections (confidence ≥ 0.5)

### CLIP Model Integration & Embedding-Based Search

#### 1. CLIP Model Loading (`clip_loader.py`)
- **Model**: OpenAI CLIP ViT-B/32
- **Backend**: OpenCLIP 2.32.0
- **Device**: Auto-detection (GPU/CPU)
- **Caching**: Google Drive integration for Colab environments

#### 2. Embedding Generation
```python
def score_prompts(self, image, prompts):
    with torch.no_grad():
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        text_input = self.tokenizer(prompts).to(self.device)
        
        image_features = self.model.encode_image(image_input)
        text_features = self.model.encode_text(text_input)
        
        # Normalize features
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Compute similarity
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        return similarity
```

#### 3. Semantic Search Capabilities
- **Text-to-Image Matching**: Natural language prompts to video content
- **Multi-Modal Understanding**: Visual and textual feature alignment
- **Zero-Shot Detection**: No training required for new object classes
- **Confidence Scoring**: Cosine similarity-based matching

### Detection Pipeline: Input → Output

#### 1. Input Processing
```
Video File → Frame Extraction → Preprocessing → CLIP Encoding
```

#### 2. Inference Pipeline
```
Frame Encoding → Text Prompt Encoding → Similarity Calculation → Confidence Scoring → Threshold Filtering
```

#### 3. Timestamp Extraction
- **Frame-based Timestamps**: Precise time positioning
- **Duration Calculation**: Video length analysis
- **Temporal Clustering**: Grouping nearby detections
- **Preview Generation**: 3-second clip extraction

#### 4. JSON Output Structure
```json
{
  "timestamp": "00:01:23.456",
  "labels": ["person", "red shirt", "walking"],
  "confidence": 0.87,
  "preview_clip": "/uploads/previews/clip_001.mp4",
  "summary": "Person in red shirt walking",
  "frame_index": 150,
  "prompt_matches": ["person", "red clothing"]
}
```

### Adjustable Confidence Threshold Implementation

#### 1. Configuration-Based Thresholds (`config.py`)
```python
CONFIDENCE_THRESHOLDS = {
    'people': 0.7,
    'colors': 0.6,
    'fire': 0.85,
    'weapons': 0.9,
    'vehicles': 0.8,
    'unusual_activity': 0.8,
}
```

#### 2. Dynamic Threshold Adjustment
- **Runtime Configuration**: YAML-based threshold management
- **Per-Detector Thresholds**: Specialized confidence levels
- **Adaptive Thresholding**: Performance-based adjustment
- **Threshold Optimization**: A/B testing for optimal values

#### 3. Threshold Testing Framework (`test_threshold_optimization.py`)
- **Automated Testing**: Multiple threshold values
- **Performance Metrics**: Detection accuracy vs. false positives
- **Statistical Analysis**: Confidence score distributions
- **Optimization Recommendations**: Data-driven threshold selection

### Dynamic Model Loading & Caching

#### 1. Model Loading System
- **CLIP ViT-B/32**: Primary semantic analysis model
- **YOLOv8 Integration**: Object detection (planned)
- **Device Auto-Detection**: GPU/CPU optimization
- **Memory Management**: Efficient model loading/unloading

#### 2. Google Drive Caching (Colab Runtime)
- **Model Persistence**: Drive-based model storage
- **Incremental Loading**: Partial model loading
- **Cache Management**: Automatic cleanup and optimization
- **Performance Optimization**: Reduced loading times

#### 3. Colab Compatibility
- **Path Management**: Environment-specific directory handling
- **Drive Integration**: Seamless cloud storage access
- **Resource Optimization**: Memory and compute efficiency
- **Error Recovery**: Robust failure handling

### Advanced Features

#### 1. Preview Clip Generation
- **Automatic Extraction**: 3-second preview clips
- **Quality Optimization**: H.264 encoding
- **Metadata Embedding**: Timestamp and detection info
- **Storage Management**: Efficient file organization

#### 2. Error Handling & Recovery
- **Comprehensive Logging**: Detailed error tracking
- **Graceful Degradation**: Fallback mechanisms
- **Retry Logic**: Automatic error recovery
- **Performance Monitoring**: Real-time metrics

#### 3. Export & Integration
- **JSON Export**: Structured result output
- **API Integration**: RESTful endpoint support
- **Real-time Processing**: Streaming analysis
- **Batch Processing**: Multiple video support

### Performance Optimizations

#### 1. Computational Efficiency
- **GPU Acceleration**: CUDA-optimized processing
- **Batch Processing**: Multiple frame analysis
- **Memory Management**: Efficient resource utilization
- **Parallel Processing**: Multi-threaded analysis

#### 2. Storage Optimization
- **Intelligent Caching**: Media registry system
- **Format Conversion**: Browser-safe MP4 output
- **Compression**: Optimized file sizes
- **Cleanup Automation**: Temporary file management

#### 3. Scalability Features
- **Horizontal Scaling**: Multi-instance support
- **Load Balancing**: Distributed processing
- **Resource Monitoring**: Performance tracking
- **Auto-scaling**: Dynamic resource allocation

This backend architecture demonstrates advanced AI/ML integration, sophisticated video processing capabilities, and enterprise-grade system design, making it an excellent showcase of technical expertise for resume documentation.
