from google.cloud import videointelligence_v1 as videointelligence
import os
import logging
import cv2
from typing import Dict, List, Any, Optional
import time
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class VideoProcessor(ABC):
    """
    Abstract base class for video processing.
    This allows for easy swapping between different video analysis providers.
    """
    
    @abstractmethod
    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """Process video and return analysis results."""
        pass

class GoogleVideoProcessor(VideoProcessor):
    """
    Google Video Intelligence API implementation.
    """
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Video Intelligence client."""
        try:
            self.client = videointelligence.VideoIntelligenceServiceClient()
            logger.info("Google Video Intelligence client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Video Intelligence client: {e}")
            raise
    
    def validate_video(self, video_path: str) -> bool:
    """
    Validate the video file using OpenCV.
    Returns True if video is valid, False otherwise.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        # Check if video has frames
        ret, _ = cap.read()
        cap.release()
        return ret
    except Exception as e:
        logger.error(f"Error validating video: {str(e)}")
        return False

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract basic video metadata using OpenCV.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration_seconds": duration,
                "resolution": f"{width}x{height}"
            }
        except Exception as e:
            logger.error(f"Error getting video metadata: {str(e)}")
            return {}

    async def process_video(self, video_path: str) -> Dict[str, Any]:
    """
    Process video using Google Video Intelligence API.
        Returns detailed analysis results including labels, objects, timestamps, and metadata.
    """
    try:
        # Validate video first
            if not self.validate_video(video_path):
            raise ValueError("Invalid or corrupted video file")
        
            # Get video metadata
            metadata = self.get_video_metadata(video_path)
        
            # Configure the request with more features
        features = [
            videointelligence.Feature.LABEL_DETECTION,
            videointelligence.Feature.OBJECT_TRACKING,
                videointelligence.Feature.SHOT_CHANGE_DETECTION,
                videointelligence.Feature.EXPLICIT_CONTENT_DETECTION,
        ]
        
        # Read the video file
        with open(video_path, "rb") as file:
            input_content = file.read()
        
        # Configure the request
        request = videointelligence.AnnotateVideoRequest(
            input_content=input_content,
            features=features,
        )
        
        # Make the request
            if self.client is None:
                raise Exception("Google Video Intelligence client not initialized")
            operation = self.client.annotate_video(request=request)
        
        # Wait for operation to complete (with timeout)
        start_time = time.time()
        while not operation.done():
            if time.time() - start_time > 180:  # 3-minute timeout
                raise TimeoutError("Video processing timed out")
            time.sleep(1)
        
        # Get the results
        result = operation.result()
        
        # Process and structure the results
        analysis = {
                "metadata": {
                    "video_path": video_path,
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "video_metadata": metadata,
                    "processor": "google_video_intelligence"
                },
            "labels": [],
                "objects": [],
                "shots": [],
                "explicit_content": [],
                "summary": {
                    "total_labels": 0,
                    "total_objects": 0,
                    "total_shots": 0,
                    "processing_time_seconds": time.time() - start_time
                }
            }
            
            # Check if we have annotation results
            if result and result.annotation_results and len(result.annotation_results) > 0:
                annotation_result = result.annotation_results[0]
        
        # Process label annotations
                if hasattr(annotation_result, 'shot_label_annotations'):
                    for annotation in annotation_result.shot_label_annotations:
            for segment in annotation.segments:
                            label_data = {
                    "label": annotation.entity.description,
                                "confidence": float(segment.confidence),
                    "start_time": segment.segment.start_time_offset.total_seconds(),
                                "end_time": segment.segment.end_time_offset.total_seconds(),
                                "duration": segment.segment.end_time_offset.total_seconds() - segment.segment.start_time_offset.total_seconds()
                            }
                            analysis["labels"].append(label_data)
        
        # Process object annotations
                if hasattr(annotation_result, 'object_annotations'):
                    for annotation in annotation_result.object_annotations:
                        object_data = {
                "label": annotation.entity.description,
                            "confidence": float(annotation.confidence),
                "start_time": annotation.segment.start_time_offset.total_seconds(),
                            "end_time": annotation.segment.end_time_offset.total_seconds(),
                            "duration": annotation.segment.end_time_offset.total_seconds() - annotation.segment.start_time_offset.total_seconds()
                        }
                        analysis["objects"].append(object_data)
                
                # Process shot changes
                if hasattr(annotation_result, 'shot_annotations'):
                    for shot in annotation_result.shot_annotations:
                        shot_data = {
                            "start_time": shot.start_time_offset.total_seconds(),
                            "end_time": shot.end_time_offset.total_seconds(),
                            "duration": shot.end_time_offset.total_seconds() - shot.start_time_offset.total_seconds()
                        }
                        analysis["shots"].append(shot_data)
                
                # Process explicit content detection
                if hasattr(annotation_result, 'explicit_annotation'):
                    for annotation in annotation_result.explicit_annotation:
                        for frame in annotation.frames:
                            explicit_data = {
                                "pornography_likelihood": annotation.pornography_likelihood.name,
                                "timestamp": frame.time_offset.total_seconds()
                            }
                            analysis["explicit_content"].append(explicit_data)
            
            # Update summary
            analysis["summary"]["total_labels"] = len(analysis["labels"])
            analysis["summary"]["total_objects"] = len(analysis["objects"])
            analysis["summary"]["total_shots"] = len(analysis["shots"])
            
            # Add confidence thresholds for filtering
            analysis["confidence_thresholds"] = {
                "high_confidence": 0.8,
                "medium_confidence": 0.5,
                "low_confidence": 0.3
            }
            
            # Add filtered results by confidence
            analysis["high_confidence_labels"] = [label for label in analysis["labels"] if label["confidence"] >= 0.8]
            analysis["high_confidence_objects"] = [obj for obj in analysis["objects"] if obj["confidence"] >= 0.8]
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise Exception(f"Video processing failed: {str(e)}") 

# Future local model implementations
class LocalModelProcessor(VideoProcessor):
    """
    Placeholder for future local model integration (CLIP, YOLO, etc.).
    """
    
    def __init__(self, model_name: str = "clip"):
        self.model_name = model_name
        logger.info(f"Local model processor initialized with {model_name}")
    
    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        Process video using local models.
        This is a placeholder for future implementation.
        """
        # TODO: Implement local model processing
        logger.warning("Local model processing not yet implemented")
        return {
            "metadata": {
                "video_path": video_path,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "processor": f"local_{self.model_name}"
            },
            "labels": [],
            "objects": [],
            "shots": [],
            "explicit_content": [],
            "summary": {
                "total_labels": 0,
                "total_objects": 0,
                "total_shots": 0,
                "processing_time_seconds": 0
            }
        }

# Global processor instance (can be swapped at runtime)
_processor: Optional[VideoProcessor] = None

def get_processor() -> VideoProcessor:
    """Get the current video processor instance."""
    global _processor
    if _processor is None:
        # Default to Google Video Intelligence
        _processor = GoogleVideoProcessor()
    return _processor

def set_processor(processor: VideoProcessor):
    """Set the video processor to use."""
    global _processor
    _processor = processor
    logger.info(f"Video processor set to: {type(processor).__name__}")

async def process_video(video_path: str) -> Dict[str, Any]:
    """
    Main function to process video using the configured processor.
    """
    processor = get_processor()
    return await processor.process_video(video_path)

# Legacy function for backward compatibility
def validate_video(video_path: str) -> bool:
    """Legacy function for video validation."""
    processor = get_processor()
    if isinstance(processor, GoogleVideoProcessor):
        return processor.validate_video(video_path)
    return True

def get_video_metadata(video_path: str) -> Dict[str, Any]:
    """Legacy function for getting video metadata."""
    processor = get_processor()
    if isinstance(processor, GoogleVideoProcessor):
        return processor.get_video_metadata(video_path)
    return {} 