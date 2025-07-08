from google.cloud import videointelligence_v1 as videointelligence
import os
import logging
import cv2
from typing import Dict, List, Any
import time

logger = logging.getLogger(__name__)

def validate_video(video_path: str) -> bool:
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

async def process_video(video_path: str) -> Dict[str, Any]:
    """
    Process video using Google Video Intelligence API.
    Returns analysis results including labels and timestamps.
    """
    try:
        # Validate video first
        if not validate_video(video_path):
            raise ValueError("Invalid or corrupted video file")
        
        # Initialize Video Intelligence client
        client = videointelligence.VideoIntelligenceServiceClient()
        
        # Configure the request
        features = [
            videointelligence.Feature.LABEL_DETECTION,
            videointelligence.Feature.OBJECT_TRACKING,
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
        operation = client.annotate_video(request=request)
        
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
            "labels": [],
            "objects": []
        }
        
        # Process label annotations
        for annotation in result.annotation_results[0].shot_label_annotations:
            for segment in annotation.segments:
                analysis["labels"].append({
                    "label": annotation.entity.description,
                    "confidence": segment.confidence,
                    "start_time": segment.segment.start_time_offset.total_seconds(),
                    "end_time": segment.segment.end_time_offset.total_seconds()
                })
        
        # Process object annotations
        for annotation in result.annotation_results[0].object_annotations:
            analysis["objects"].append({
                "label": annotation.entity.description,
                "confidence": annotation.confidence,
                "start_time": annotation.segment.start_time_offset.total_seconds(),
                "end_time": annotation.segment.end_time_offset.total_seconds()
            })
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise Exception(f"Video processing failed: {str(e)}") 