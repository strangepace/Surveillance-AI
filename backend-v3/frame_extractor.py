# backend_v3/frame_extractor.py
"""
Video frame extraction module for backend-v3.
Extracts frames from videos with configurable sampling rate and saves as JPG files.
"""
import os
import cv2
from PIL import Image
import numpy as np
from typing import List, Dict, Any, Optional
from config_loader import load_clip_config


def extract_frames(video_path: str, output_dir: str, sampling_rate: int = 1, 
                  resize: bool = False, return_images: bool = False) -> List[Dict[str, Any]]:
    """
    Extract frames from video file and save as JPG images.
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save extracted frames
        sampling_rate (int): Extract every Nth frame (1 = every frame, 15 = every 15th frame)
        resize (bool): Whether to resize frames to 224x224
        return_images (bool): Whether to return PIL Image objects in metadata
    
    Returns:
        List[Dict[str, Any]]: List of frame metadata with paths and timestamps
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        RuntimeError: If video cannot be opened
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"📹 Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
    print(f"🔍 Extracting every {sampling_rate} frame(s)...")
    
    frame_metadata = []
    frame_count = 0
    extracted_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract frame based on sampling rate
        if frame_count % sampling_rate == 0:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize if requested
            if resize:
                frame_rgb = cv2.resize(frame_rgb, (224, 224))
            
            # Calculate timestamp
            timestamp_seconds = frame_count / fps
            timestamp_str = format_timestamp(timestamp_seconds)
            
            # Create filename
            filename = f"frame_{int(timestamp_seconds):03d}.jpg"
            frame_path = os.path.join(output_dir, filename)
            
            # Save frame as JPG
            pil_image = Image.fromarray(frame_rgb)
            pil_image.save(frame_path, 'JPEG', quality=95)
            
            # Create metadata
            metadata = {
                "frame_path": frame_path,
                "timestamp": timestamp_str,
                "timestamp_seconds": timestamp_seconds,
                "frame_number": frame_count
            }
            
            # Add PIL Image object if requested
            if return_images:
                metadata["image"] = pil_image
            
            frame_metadata.append(metadata)
            extracted_count += 1
            
            # Log progress every 10 frames
            if extracted_count % 10 == 0:
                print(f"  ✅ Extracted {extracted_count} frames...")
        
        frame_count += 1
    
    cap.release()
    
    print(f"🎉 Frame extraction complete: {extracted_count} frames extracted")
    print(f"📁 Frames saved to: {output_dir}")
    
    return frame_metadata


def format_timestamp(seconds: float) -> str:
    """
    Format seconds into HH:MM:SS timestamp string.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp (HH:MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def extract_frames_with_config(video_path: str, config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract frames using configuration from YAML file.
    
    Args:
        video_path (str): Path to the video file
        config_path (str): Path to config file (optional)
        
    Returns:
        List[Dict[str, Any]]: List of frame metadata
    """
    # Load config
    config = load_clip_config(config_path)
    
    # Get frame extraction settings from config (with defaults)
    frame_config = config.get('frame_extraction', {})
    sampling_rate = frame_config.get('sampling_rate', 1)
    output_dir = frame_config.get('output_dir', 'content/frames')
    resize = frame_config.get('resize', False)
    
    return extract_frames(video_path, output_dir, sampling_rate, resize)


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Get video information without extracting frames.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        Dict[str, Any]: Video information
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    cap.release()
    
    return {
        "fps": fps,
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration": duration,
        "duration_formatted": format_timestamp(duration)
    } 