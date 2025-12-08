"""
Live Source - Frame ingestion for live stream processing.

Reads frames from video sources (RTSP, file, camera) at a controlled rate
and feeds them into a queue for processing.
"""

import cv2
import time
import logging
import threading
import numpy as np
from typing import Optional, Tuple, Callable
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("live_source")


class SourceType(Enum):
    """Type of video source."""
    RTSP = "rtsp"
    FILE = "file"
    CAMERA = "camera"


@dataclass
class FrameData:
    """Frame data with metadata."""
    frame: np.ndarray  # OpenCV frame (numpy array)
    timestamp_seconds: float  # Relative timestamp in seconds
    frame_number: int  # Sequential frame number
    source_timestamp: Optional[float] = None  # Absolute timestamp if available


class LiveSource:
    """
    Live video source that continuously reads frames.
    
    Supports:
    - RTSP streams (rtsp://...)
    - Video files (for simulation/testing)
    - Camera devices (device index)
    """
    
    def __init__(
        self,
        source: str,
        source_type: Optional[SourceType] = None,
        target_fps: float = 1.0,
        max_queue_size: int = 100
    ):
        """
        Initialize live source.
        
        Args:
            source (str): Source URL/path (RTSP URL, file path, or camera index)
            source_type (Optional[SourceType]): Explicit source type, or auto-detect
            target_fps (float): Target frames per second to sample (default: 1.0)
            max_queue_size (int): Maximum queue size for frames (default: 100)
        """
        self.source = source
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 1.0
        self.max_queue_size = max_queue_size
        
        # Auto-detect source type if not provided
        if source_type is None:
            if source.startswith("rtsp://"):
                self.source_type = SourceType.RTSP
            elif source.startswith("http://") or source.startswith("https://"):
                self.source_type = SourceType.RTSP  # Treat HTTP streams as RTSP-like
            elif source.isdigit():
                self.source_type = SourceType.CAMERA
                self.source = int(source)  # Convert to int for camera index
            else:
                self.source_type = SourceType.FILE
        else:
            self.source_type = source_type
            if source_type == SourceType.CAMERA and source.isdigit():
                self.source = int(source)
        
        # State
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_queue: Queue = Queue(maxsize=max_queue_size)
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.frame_counter = 0
        self.start_time: Optional[float] = None
        
        # Video properties (for file sources)
        self.video_fps: Optional[float] = None
        self.video_total_frames: Optional[int] = None
        
        logger.info(f"LiveSource initialized: type={self.source_type.value}, source={self.source}, target_fps={target_fps}")
    
    def _open_source(self) -> bool:
        """Open the video source."""
        try:
            if self.source_type == SourceType.CAMERA:
                self.cap = cv2.VideoCapture(self.source)
            else:
                self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open source: {self.source}")
                logger.error("Please check:")
                logger.error("  - File path is correct (for file sources)")
                logger.error("  - RTSP URL is accessible (for RTSP sources)")
                logger.error("  - Camera device is available (for camera sources)")
                return False
            
            # Get video properties (for file sources)
            if self.source_type == SourceType.FILE:
                self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
                self.video_total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if self.video_fps > 0:
                    logger.info(f"Video file: {self.video_total_frames} frames @ {self.video_fps:.2f} fps")
                else:
                    logger.warning("Could not determine video FPS - using default timing")
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening source: {e}", exc_info=True)
            logger.error("Live source will not start. Please check configuration and source availability.")
            return False
    
    def _close_source(self):
        """Close the video source."""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def _capture_loop(self):
        """Main capture loop running in background thread."""
        logger.info("Capture loop started")
        self.start_time = time.time()
        last_frame_time = 0.0
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    if self.source_type == SourceType.FILE:
                        # End of video file - stop gracefully
                        logger.info("End of video file reached - stopping capture")
                        break
                    else:
                        # Stream issue - wait and retry (with max retries)
                        logger.warning("Failed to read frame from stream, retrying...")
                        time.sleep(0.1)
                        # Check if we should continue retrying
                        # For now, continue indefinitely for streams
                        continue
                
                # Control frame rate
                current_time = time.time()
                elapsed = current_time - last_frame_time
                
                if elapsed < self.frame_interval:
                    # Skip frame to maintain target FPS
                    continue
                
                last_frame_time = current_time
                
                # Calculate relative timestamp
                if self.start_time:
                    relative_timestamp = current_time - self.start_time
                else:
                    relative_timestamp = 0.0
                
                # Create frame data
                frame_data = FrameData(
                    frame=frame.copy(),  # Copy to avoid reference issues
                    timestamp_seconds=relative_timestamp,
                    frame_number=self.frame_counter,
                    source_timestamp=current_time
                )
                
                # Add to queue (non-blocking, drop if full)
                try:
                    self.frame_queue.put_nowait(frame_data)
                    self.frame_counter += 1
                except:
                    # Queue full - drop frame
                    logger.warning(f"Frame queue full, dropping frame {self.frame_counter}")
                
                # Small sleep to prevent tight loop
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}", exc_info=True)
                time.sleep(0.1)
        
        logger.info("Capture loop stopped")
        self._close_source()
    
    def start(self) -> bool:
        """
        Start capturing frames.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("LiveSource is already running")
            return False
        
        if not self._open_source():
            return False
        
        self.is_running = True
        self.frame_counter = 0
        self.start_time = None
        
        # Start capture thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        logger.info("LiveSource started")
        return True
    
    def stop(self):
        """Stop capturing frames."""
        if not self.is_running:
            return
        
        logger.info("Stopping LiveSource...")
        self.is_running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        self._close_source()
        logger.info("LiveSource stopped")
    
    def get_frame(self, timeout: Optional[float] = None) -> Optional[FrameData]:
        """
        Get next frame from queue.
        
        Args:
            timeout (Optional[float]): Timeout in seconds (None = blocking)
            
        Returns:
            Optional[FrameData]: Frame data or None if timeout/empty
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_frame_count(self) -> int:
        """Get total number of frames captured."""
        return self.frame_counter
    
    def is_active(self) -> bool:
        """Check if source is actively capturing."""
        return self.is_running and (self.thread is None or self.thread.is_alive())
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.frame_queue.qsize()

