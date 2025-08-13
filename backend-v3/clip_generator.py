# backend_v3/clip_generator.py
"""
Preview clip generation module for backend-v3.
Generates short video clips around detection timestamps for review and analysis.
"""
import os
import cv2
import re
from typing import Tuple, Optional


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
    Generate a preview clip around a detection timestamp.
    
    Args:
        video_path (str): Path to the original video file
        output_dir (str): Directory to save the preview clip
        timestamp (str): Detection timestamp in "HH:MM:SS" format (e.g., "00:02:15")
        clip_length (int): Total length of preview in seconds (default = 5)
        
    Returns:
        str: Full path to the saved preview clip
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If timestamp format is invalid
        RuntimeError: If video cannot be opened or processed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert timestamp to seconds
    target_seconds = timestamp_to_seconds(timestamp)
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0
    
    print(f"📹 Video info: {total_frames} frames, {fps:.2f} fps, {video_duration:.2f}s duration")
    print(f"🎯 Target timestamp: {timestamp} ({target_seconds}s)")
    print(f"⏱️  Generating {clip_length}s preview clip...")
    
    # Calculate clip start and end times
    half_clip = clip_length // 2
    clip_start_seconds = max(0, target_seconds - half_clip)
    clip_end_seconds = min(video_duration, target_seconds + half_clip)
    
    # Adjust if near video boundaries
    if clip_start_seconds == 0:
        clip_end_seconds = min(clip_length, video_duration)
    elif clip_end_seconds == video_duration:
        clip_start_seconds = max(0, video_duration - clip_length)
    
    # Convert to frame numbers
    start_frame = int(clip_start_seconds * fps)
    end_frame = int(clip_end_seconds * fps)
    
    print(f"📅 Clip range: {seconds_to_timestamp(clip_start_seconds)} - {seconds_to_timestamp(clip_end_seconds)}")
    print(f"🎞️  Frame range: {start_frame} - {end_frame}")
    
    # Create output filename
    timestamp_clean = timestamp.replace(":", "_")
    output_filename = f"clip_{timestamp_clean}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    # Get video codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise RuntimeError(f"Could not create output video file: {output_path}")
    
    # Extract frames for the clip
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frames_written = 0
    
    for frame_num in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        
        out.write(frame)
        frames_written += 1
        
        # Log progress every 30 frames
        if frames_written % 30 == 0:
            print(f"  ✅ Written {frames_written} frames...")
    
    # Clean up
    cap.release()
    out.release()
    
    # Verify the clip was created
    if not os.path.exists(output_path):
        raise RuntimeError(f"Preview clip was not created: {output_path}")
    
    actual_duration = frames_written / fps
    print(f"🎉 Preview clip created: {output_path}")
    print(f"📊 Actual duration: {actual_duration:.2f}s ({frames_written} frames)")
    
    return output_path


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