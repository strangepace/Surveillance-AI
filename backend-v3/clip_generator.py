# backend_v3/clip_generator.py
"""
Preview clip generation module for backend-v3.
Generates short video clips around detection timestamps for review and analysis.
Uses ffmpeg for browser-compatible video encoding (H.264 MP4 + VP9 WebM fallback).
"""
import os
import cv2
import re
import logging
from typing import Tuple, Optional
from utils.ffmpeg import transcode_segment, has_ffmpeg

logger = logging.getLogger(__name__)


def timestamp_to_seconds(timestamp: str) -> int:
    """
    Convert timestamp string in "HH:MM:SS" format to total seconds.
    
    Args:
        timestamp (str): Timestamp in "HH:MM:SS" format
        
    Returns:
        int: Total seconds
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    # Validate timestamp format
    pattern = r'^(\d{2}):(\d{2}):(\d{2})$'
    match = re.match(pattern, timestamp)
    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}. Expected HH:MM:SS")
    
    hours, minutes, seconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_timestamp(seconds: float) -> str:
    """
    Convert total seconds to "HH:MM:SS" format.
    
    Args:
        seconds (float): Total seconds
        
    Returns:
        str: Timestamp in "HH:MM:SS" format
    """
    seconds = int(seconds)  # Ensure it's an integer
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def generate_preview_clip(video_path: str, output_dir: str, timestamp: str, 
                         clip_length: int = 5) -> str:
    """
    Generate a preview clip around a detection timestamp using ffmpeg.
    
    Args:
        video_path (str): Path to the original video file
        output_dir (str): Directory to save the preview clip
        timestamp (str): Detection timestamp in "HH:MM:SS" format (e.g., "00:02:15")
        clip_length (int): Total length of preview in seconds (default = 5)
        
    Returns:
        str: Full path to the saved preview clip (MP4 if available, WebM otherwise)
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If timestamp format is invalid
        RuntimeError: If video cannot be processed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert timestamp to seconds
    target_seconds = timestamp_to_seconds(timestamp)
    
    # Check ffmpeg availability
    if not has_ffmpeg():
        logger.warning("FFmpeg not available - preview clips cannot be generated")
        raise RuntimeError("FFmpeg not available for video transcoding")
    
    # Get video properties using OpenCV (just for info, not for writing)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    try:
        fps_value = float(fps)
    except Exception:
        fps_value = 30.0  # safe default
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps_value if fps_value > 0 else 0
    cap.release()
    
    logger.info(f"📹 Video info: {total_frames} frames, {fps_value:.2f} fps, {video_duration:.2f}s duration")
    logger.info(f"🎯 Target timestamp: {timestamp} ({target_seconds}s)")
    
    # Calculate clip boundaries
    clip_half_length = clip_length / 2
    start_seconds = max(0, target_seconds - clip_half_length)
    end_seconds = min(video_duration, target_seconds + clip_half_length)
    
    logger.info(f"🎬 Clip boundaries: {start_seconds:.1f}s - {end_seconds:.1f}s")
    
    # Create output filenames
    timestamp_clean = timestamp.replace(":", "_")
    output_mp4 = os.path.join(output_dir, f"clip_{timestamp_clean}.mp4")
    output_webm = os.path.join(output_dir, f"clip_{timestamp_clean}.webm")
    
    # Normalize paths to forward slashes for consistency
    output_mp4 = output_mp4.replace("\\", "/")
    output_webm = output_webm.replace("\\", "/")
    
    # Use ffmpeg to transcode the video segment
    logger.info(f"🔄 Transcoding video segment using ffmpeg...")
    mp4_success, webm_success = transcode_segment(
        src=video_path,
        start_sec=start_seconds,
        duration=end_seconds - start_seconds,
        out_mp4=output_mp4,
        out_webm=output_webm,
        codec="h264"
    )
    
    # Determine which file to return
    if mp4_success:
        logger.info(f"✅ Preview clip created (H.264 MP4): {output_mp4}")
        return output_mp4
    elif webm_success:
        logger.info(f"✅ Preview clip created (VP9 WebM): {output_webm}")
        return output_webm
    else:
        raise RuntimeError(f"Failed to generate preview clip: neither MP4 nor WebM was created")


def generate_preview_clips_batch(video_path: str, output_dir: str, 
                                timestamps: list, clip_length: int = 5) -> list:
    """
    Generate multiple preview clips for a list of timestamps.
    
    Args:
        video_path (str): Path to the original video file
        output_dir (str): Directory to save the preview clips
        timestamps (list): List of timestamps in "HH:MM:SS" format
        clip_length (int): Total length of each preview in seconds
        
    Returns:
        list: List of paths to the generated preview clips
    """
    clip_paths = []
    
    for i, timestamp in enumerate(timestamps):
        try:
            clip_path = generate_preview_clip(video_path, output_dir, timestamp, clip_length)
            clip_paths.append(clip_path)
            print(f"✅ Generated clip {i+1}/{len(timestamps)}: {timestamp}")
        except Exception as e:
            print(f"❌ Failed to generate clip for {timestamp}: {e}")
            clip_paths.append(None)
    
    return clip_paths


def get_clip_info(clip_path: str) -> dict:
    """
    Get information about a generated preview clip.
    
    Args:
        clip_path (str): Path to the preview clip
        
    Returns:
        dict: Clip information (duration, fps, dimensions, etc.)
    """
    if not os.path.exists(clip_path):
        raise FileNotFoundError(f"Clip file not found: {clip_path}")
    
    cap = cv2.VideoCapture(clip_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open clip file: {clip_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    cap.release()
    
    return {
        "path": clip_path,
        "fps": fps,
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration": duration,
        "duration_formatted": seconds_to_timestamp(int(duration)),
        "file_size_mb": os.path.getsize(clip_path) / (1024 * 1024)
    }
