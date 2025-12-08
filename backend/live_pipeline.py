"""
Live Pipeline - Main orchestrator for live stream processing.

Coordinates LiveSource and LiveDetector to create a complete
real-time detection pipeline.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Callable
from queue import Queue

from live_source import LiveSource, SourceType
from live_detector import LiveDetector, Alert

logger = logging.getLogger("live_pipeline")


class LivePipeline:
    """
    Main pipeline for live stream processing.
    
    Coordinates:
    - LiveSource: Frame ingestion
    - LiveDetector: Detection processing
    - Alert queue: Output for alerts
    """
    
    def __init__(
        self,
        source: str,
        prompts: List[str],
        config: Optional[Dict[str, Any]] = None,
        source_type: Optional[SourceType] = None,
        target_fps: float = 1.0,
        similarity_threshold: float = 0.21,
        max_frame_queue_size: int = 100,
        max_alert_queue_size: int = 1000
    ):
        """
        Initialize live pipeline.
        
        Args:
            source (str): Video source (RTSP URL, file path, or camera index)
            prompts (List[str]): Detection prompts
            config (Optional[Dict[str, Any]]): Configuration dictionary
            source_type (Optional[SourceType]): Explicit source type
            target_fps (float): Target frame sampling rate (default: 1.0)
            similarity_threshold (float): CLIP similarity threshold (default: 0.21)
            max_frame_queue_size (int): Max size for frame queue (default: 100)
            max_alert_queue_size (int): Max size for alert queue (default: 1000)
        """
        self.source = source
        self.prompts = prompts
        self.config = config or {}
        self.target_fps = target_fps
        self.similarity_threshold = similarity_threshold
        
        # Create queues
        self.frame_queue = Queue(maxsize=max_frame_queue_size)
        self.alert_queue = Queue(maxsize=max_alert_queue_size)
        
        # Create components
        self.live_source = LiveSource(
            source=source,
            source_type=source_type,
            target_fps=target_fps,
            max_queue_size=max_frame_queue_size
        )
        
        self.live_detector = LiveDetector(
            prompts=prompts,
            config=config,
            similarity_threshold=similarity_threshold
        )
        
        # State
        self.is_running = False
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        logger.info(f"LivePipeline initialized: source={source}, prompts={len(prompts)}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """
        Add callback function for alerts.
        
        Args:
            callback (Callable[[Alert], None]): Function to call when alert is emitted
        """
        self.alert_callbacks.append(callback)
    
    def _alert_callback_wrapper(self, alert: Alert):
        """Wrapper to call all registered callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}", exc_info=True)
    
    async def start(self) -> bool:
        """
        Start the live pipeline.
        
        Returns:
            bool: True if started successfully
        """
        if self.is_running:
            logger.warning("LivePipeline is already running")
            return False
        
        logger.info("Starting LivePipeline...")
        
        # Start live source
        if not self.live_source.start():
            logger.error("Failed to start LiveSource")
            return False
        
        # Start live detector
        if not await self.live_detector.start(
            frame_queue=self.frame_queue,
            alert_queue=self.alert_queue,
            alert_callback=self._alert_callback_wrapper
        ):
            logger.error("Failed to start LiveDetector")
            self.live_source.stop()
            return False
        
        # Transfer frames from source to detector queue
        # This runs in a background task
        asyncio.create_task(self._frame_transfer_loop())
        
        self.is_running = True
        logger.info("LivePipeline started")
        return True
    
    async def _frame_transfer_loop(self):
        """Transfer frames from source to detector queue."""
        logger.info("Frame transfer loop started")
        
        while self.is_running:
            try:
                # Get frame from source
                frame_data = self.live_source.get_frame(timeout=0.1)
                
                if frame_data:
                    # Add to detector queue
                    try:
                        self.frame_queue.put_nowait(frame_data)
                    except:
                        logger.warning("Frame queue full, dropping frame")
                
                # Small sleep to prevent tight loop
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in frame transfer loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)
        
        logger.info("Frame transfer loop stopped")
    
    def stop(self):
        """Stop the live pipeline."""
        if not self.is_running:
            return
        
        logger.info("Stopping LivePipeline...")
        self.is_running = False
        
        # Stop components
        self.live_detector.stop()
        self.live_source.stop()
        
        logger.info("LivePipeline stopped")
    
    def get_alert(self, timeout: Optional[float] = None) -> Optional[Alert]:
        """
        Get next alert from queue.
        
        Args:
            timeout (Optional[float]): Timeout in seconds (None = blocking)
            
        Returns:
            Optional[Alert]: Alert or None if timeout/empty
        """
        try:
            return self.alert_queue.get(timeout=timeout)
        except:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        source_stats = {
            "frames_captured": self.live_source.get_frame_count(),
            "queue_size": self.live_source.get_queue_size(),
            "is_active": self.live_source.is_active()
        }
        
        detector_stats = self.live_detector.get_stats()
        
        return {
            "is_running": self.is_running,
            "source": source_stats,
            "detector": detector_stats,
            "alert_queue_size": self.alert_queue.qsize()
        }


async def create_pipeline_from_config(
    config: Dict[str, Any],
    prompts: Optional[List[str]] = None
) -> Optional[LivePipeline]:
    """
    Create LivePipeline from configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        prompts (Optional[List[str]]): Override prompts from config
        
    Returns:
        Optional[LivePipeline]: Pipeline instance or None if config invalid
    """
    try:
        live_config = config.get('live_stream', {})
        
        # Get source
        source = live_config.get('source')
        if not source:
            logger.error("live_stream.source not found in config")
            return None
        
        # Get source type
        source_type_str = live_config.get('source_type')
        source_type = None
        if source_type_str:
            source_type = SourceType(source_type_str.lower())
        
        # Get prompts (from config or parameter)
        if prompts is None:
            prompts = live_config.get('prompts', [])
        
        if not prompts:
            logger.error("No prompts specified")
            return None
        
        # Get settings
        target_fps = live_config.get('target_fps', 1.0)
        similarity_threshold = config.get('detection', {}).get('similarity_threshold', 0.21)
        max_frame_queue = live_config.get('max_frame_queue_size', 100)
        max_alert_queue = live_config.get('max_alert_queue_size', 1000)
        
        # Create pipeline
        pipeline = LivePipeline(
            source=source,
            prompts=prompts,
            config=config,
            source_type=source_type,
            target_fps=target_fps,
            similarity_threshold=similarity_threshold,
            max_frame_queue_size=max_frame_queue,
            max_alert_queue_size=max_alert_queue
        )
        
        logger.info(f"Created pipeline from config: source={source}, prompts={len(prompts)}")
        return pipeline
        
    except Exception as e:
        logger.error(f"Failed to create pipeline from config: {e}", exc_info=True)
        return None

