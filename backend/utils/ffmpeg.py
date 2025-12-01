#!/usr/bin/env python3
"""
FFmpeg utility module for backend.
Provides browser-compatible video transcoding using ffmpeg CLI.
Cross-platform compatible with bundled binaries and automatic fallbacks.
"""
import os
import shutil
import subprocess
import logging
import platform
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_ffmpeg_bundled_path() -> Optional[str]:
    """
    Get path to bundled FFmpeg binary for current platform.
    Returns None if bundled version not found.
    """
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if platform.system() == "Windows":
        ffmpeg_path = os.path.join(current_dir, "ffmpeg", "windows", "bin", "ffmpeg.exe")
    elif platform.system() == "Linux":
        ffmpeg_path = os.path.join(current_dir, "ffmpeg", "linux", "bin", "ffmpeg")
    elif platform.system() == "Darwin":  # macOS
        ffmpeg_path = os.path.join(current_dir, "ffmpeg", "macos", "bin", "ffmpeg")
    else:
        logger.warning(f"Unsupported platform: {platform.system()}")
        return None
    
    if os.path.exists(ffmpeg_path):
        logger.info(f"Found bundled FFmpeg: {ffmpeg_path}")
        return ffmpeg_path
    
    logger.debug(f"Bundled FFmpeg not found at: {ffmpeg_path}")
    return None


def get_ffmpeg_system_path() -> Optional[str]:
    """
    Get path to system-installed FFmpeg.
    Returns None if not found in system PATH.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        logger.info(f"Found system FFmpeg: {ffmpeg_path}")
        return ffmpeg_path
    
    logger.debug("System FFmpeg not found in PATH")
    return None


def has_ffmpeg() -> bool:
    """
    Check if FFmpeg is available (bundled or system).
    Automatically configures environment if needed.
    """
    # First check if we already have a working FFmpeg
    if get_ffmpeg_system_path():
        return True
    
    # Check for bundled version
    bundled_path = get_ffmpeg_bundled_path()
    if bundled_path:
        # Add bundled FFmpeg to current session PATH
        ffmpeg_dir = os.path.dirname(bundled_path)
        current_path = os.environ.get('PATH', '')
        
        if ffmpeg_dir not in current_path:
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
            logger.info(f"Added bundled FFmpeg to PATH: {ffmpeg_dir}")
        
        return True
    
    logger.warning("No FFmpeg available (neither bundled nor system)")
    return False


def transcode_segment(
    src: str, 
    start_sec: float, 
    duration: float, 
    out_mp4: str, 
    out_webm: Optional[str] = None, 
    codec: str = "h264"
) -> Tuple[bool, bool]:
    """
    Transcode a video segment to browser-compatible formats.
    
    Args:
        src: Source video file path
        start_sec: Start time in seconds
        duration: Duration in seconds
        out_mp4: Output MP4 file path (H.264)
        out_webm: Output WebM file path (VP9, optional)
        codec: Preferred codec ("h264" or "vp9")
    
    Returns:
        Tuple of (mp4_success, webm_success)
    """
    if not has_ffmpeg():
        logger.warning("FFmpeg not available, cannot transcode video segments")
        return False, False
    
    mp4_success = False
    webm_success = False
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    if out_webm:
        os.makedirs(os.path.dirname(out_webm), exist_ok=True)
    
    # Get the FFmpeg executable path
    ffmpeg_exe = get_ffmpeg_system_path() or get_ffmpeg_bundled_path()
    if not ffmpeg_exe:
        logger.error("Could not locate FFmpeg executable")
        return False, False
    
    # Generate H.264 MP4 (primary format)
    if codec == "h264" or codec == "auto":
        try:
            cmd = [
                ffmpeg_exe, '-y',  # Overwrite output
                '-loglevel', 'error',  # Minimal logging
                '-ss', str(start_sec),  # Start time
                '-t', str(duration),   # Duration
                '-i', src,             # Input file
                '-an',                 # No audio
                '-c:v', 'libx264',     # H.264 codec
                '-preset', 'veryfast', # Fast encoding
                '-crf', '28',          # Good quality
                '-pix_fmt', 'yuv420p', # Browser-compatible pixel format
                '-profile:v', 'baseline', # Baseline profile for compatibility
                '-level', '3.0',       # Level 3.0 for broad support
                '-movflags', '+faststart', # Optimize for web streaming
                '-vf', 'scale=iw:ih:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2',  # Ensure even dimensions
                out_mp4
            ]
            
            logger.debug(f"FFmpeg H.264 command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(out_mp4):
                mp4_success = True
                logger.info(f"✅ H.264 MP4 generated successfully: {out_mp4}")
            else:
                logger.error(f"❌ H.264 MP4 generation failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ H.264 MP4 generation timed out")
        except Exception as e:
            logger.error(f"❌ H.264 MP4 generation error: {e}")
    
    # Generate VP9 WebM (fallback format)
    if out_webm and (not mp4_success or codec == "vp9"):
        try:
            cmd = [
                ffmpeg_exe, '-y',  # Overwrite output
                '-loglevel', 'error',  # Minimal logging
                '-ss', str(start_sec),  # Start time
                '-t', str(duration),   # Duration
                '-i', src,             # Input file
                '-an',                 # No audio
                '-c:v', 'libvpx-vp9',  # VP9 codec
                '-b:v', '1M',          # Target bitrate
                '-pix_fmt', 'yuv420p', # Browser-compatible pixel format
                '-row-mt', '1',        # Multi-threading
                '-vf', 'scale=iw:ih:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2',  # Ensure even dimensions
                out_webm
            ]
            
            logger.debug(f"FFmpeg VP9 command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(out_webm):
                webm_success = True
                logger.info(f"✅ VP9 WebM generated successfully: {out_webm}")
            else:
                logger.error(f"❌ VP9 WebM generation failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ VP9 WebM generation timed out")
        except Exception as e:
            logger.error(f"❌ VP9 WebM generation error: {e}")
    
    return mp4_success, webm_success


def get_video_info(video_path: str) -> Optional[dict]:
    """
    Get video information using ffprobe.
    
    Args:
        video_path: Path to video file
    
    Returns:
        Dictionary with video info or None if failed
    """
    if not has_ffmpeg():
        return None
    
    # Get the ffprobe executable path
    ffmpeg_dir = os.path.dirname(get_ffmpeg_system_path() or get_ffmpeg_bundled_path() or "")
    if platform.system() == "Windows":
        ffprobe_exe = os.path.join(ffmpeg_dir, "ffprobe.exe")
    else:
        ffprobe_exe = os.path.join(ffmpeg_dir, "ffprobe")
    
    if not os.path.exists(ffprobe_exe):
        logger.error(f"FFprobe not found at: {ffprobe_exe}")
        return None
    
    try:
        cmd = [
            ffprobe_exe, '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        else:
            logger.error(f"FFprobe failed: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"FFprobe error: {e}")
        return None


def clip_video_segment(
    src: str, 
    start_sec: float, 
    end_sec: float, 
    output_path: str,
    codec: str = "copy"
) -> bool:
    """
    Clip a video segment using FFmpeg.
    
    Args:
        src: Source video file path
        start_sec: Start time in seconds
        end_sec: End time in seconds
        output_path: Output file path
        codec: Codec to use ("copy" for fast, "libx264" for reencode)
        
    Returns:
        True if successful, False otherwise
    """
    if not has_ffmpeg():
        logger.error("FFmpeg not available for video clipping")
        return False
    
    ffmpeg_exe = get_ffmpeg_system_path() or get_ffmpeg_bundled_path()
    if not ffmpeg_exe:
        logger.error("Could not find FFmpeg executable")
        return False
    
    duration = end_sec - start_sec
    
    try:
        if codec == "copy":
            # Fast copy mode - try first
            cmd = [
                ffmpeg_exe, '-y', '-loglevel', 'error',
                '-ss', str(start_sec),
                '-t', str(duration),
                '-i', src,
                '-c', 'copy',  # Copy streams without reencoding
                output_path
            ]
            
            logger.info(f"FFmpeg clip command (copy): {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Video clipped successfully with copy codec: {output_path}")
                return True
            else:
                logger.warning(f"Copy codec failed, falling back to reencode: {result.stderr}")
        
        # Fallback to reencode mode
        cmd = [
            ffmpeg_exe, '-y', '-loglevel', 'error',
            '-ss', str(start_sec),
            '-t', str(duration),
            '-i', src,
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-movflags', '+faststart',
            output_path
        ]
        
        logger.info(f"FFmpeg clip command (reencode): {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"Video clipped successfully with reencode: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg clipping failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg clipping timed out")
        return False
    except Exception as e:
        logger.error(f"FFmpeg clipping error: {e}")
        return False


def setup_ffmpeg_environment():
    """
    Setup FFmpeg environment automatically.
    Called during application startup to ensure FFmpeg is available.
    """
    if has_ffmpeg():
        logger.info("✅ FFmpeg environment configured successfully")
        return True
    else:
        logger.warning("⚠️  FFmpeg not available - preview generation will be limited")
        return False

