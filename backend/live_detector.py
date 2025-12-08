"""
Live Detector - Real-time detection engine for live streams.

Processes frames from a queue, runs CLIP-based detection,
and emits alerts when detections are found.
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from queue import Queue, Empty
from dataclasses import dataclass, asdict
import torch
import numpy as np
import cv2
from PIL import Image

from clip_loader import get_clip_model
from prompt_interpreter import interpret_multiple_prompts
from live_source import FrameData

logger = logging.getLogger("live_detector")


@dataclass
class Alert:
    """
    Alert emitted when a detection is found.
    """
    timestamp_seconds: float  # Relative timestamp in stream
    frame_number: int  # Frame number
    labels: List[str]  # Detected labels
    confidence: float  # Confidence score (0-1)
    category: Optional[str] = None  # Alert category/type
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return asdict(self)


class LiveDetector:
    """
    Live detection engine that processes frames and emits alerts.
    
    Uses CLIP model for semantic detection matching user prompts.
    """
    
    def __init__(
        self,
        prompts: List[str],
        config: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.21,
        config_path: Optional[str] = None
    ):
        """
        Initialize live detector.
        
        Args:
            prompts (List[str]): Detection prompts (e.g., ["person", "car", "fire"])
            config (Optional[Dict[str, Any]]): Configuration dictionary
            similarity_threshold (float): CLIP similarity threshold (default: 0.21)
            config_path (Optional[str]): Path to config file (alternative to config dict)
        """
        self.prompts = prompts
        self.config = config or {}
        self.similarity_threshold = similarity_threshold
        
        # Load config if path provided
        if config_path:
            import yaml
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                self.similarity_threshold = self.config.get('detection', {}).get('similarity_threshold', 0.21)
        
        # CLIP model (lazy loaded)
        self.clip_model = None
        self.clip_tokenizer = None
        self.clip_preprocess = None
        self.device = None
        
        # Text features (encoded prompts)
        self.text_features: Optional[torch.Tensor] = None
        self.text_labels: List[str] = []
        
        # State
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.frame_queue: Optional[Queue] = None
        self.alert_queue: Optional[Queue] = None
        self.alert_callback: Optional[Callable[[Alert], None]] = None
        
        # Statistics
        self.frames_processed = 0
        self.alerts_emitted = 0
        
        logger.info(f"LiveDetector initialized with {len(prompts)} prompts, threshold={similarity_threshold}")
    
    def _load_clip_model(self):
        """Load CLIP model (lazy initialization)."""
        if self.clip_model is not None:
            return
        
        try:
            config_path = self.config.get('_config_path', 'config/clip_config.yaml')
            self.clip_model, self.clip_tokenizer, self.clip_preprocess, self.device = get_clip_model(
                config_path=config_path
            )
            logger.info(f"CLIP model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}", exc_info=True)
            raise
    
    async def _prepare_prompts(self):
        """Prepare and encode text prompts."""
        try:
            # Interpret prompts to get labels
            prompt_categories = await interpret_multiple_prompts(self.prompts)
            
            # Extract labels
            all_labels = []
            for category_info in prompt_categories:
                labels = category_info.get("labels", [])
                if labels:
                    all_labels.extend(labels)
                else:
                    prompt = category_info.get("prompt", "")
                    all_labels.append(prompt)
            
            self.text_labels = list(set(all_labels))  # Remove duplicates
            logger.info(f"Prepared {len(self.text_labels)} labels: {self.text_labels}")
            
            # Encode text prompts
            self._load_clip_model()
            text_tokens = self.clip_tokenizer(self.text_labels).to(self.device)
            
            with torch.no_grad():
                self.text_features = self.clip_model.encode_text(text_tokens)
            
            logger.info(f"Encoded {len(self.text_labels)} text prompts")
            
        except Exception as e:
            logger.error(f"Failed to prepare prompts: {e}", exc_info=True)
            raise
    
    def _process_frame(self, frame_data: FrameData) -> Optional[Alert]:
        """
        Process a single frame and return alert if detection found.
        
        Args:
            frame_data (FrameData): Frame data to process
            
        Returns:
            Optional[Alert]: Alert if detection found, None otherwise
        """
        if self.text_features is None:
            logger.warning("Text features not prepared, skipping frame")
            return None
        
        try:
            # Convert frame to PIL Image
            frame_rgb = cv2.cvtColor(frame_data.frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Preprocess and encode frame
            image_input = self.clip_preprocess(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features_norm = self.text_features / self.text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarities
            similarities = (100.0 * image_features @ text_features_norm.T).softmax(dim=-1)
            similarities = similarities.squeeze().cpu().numpy()
            
            # Find matches above threshold
            matches = []
            for i, label in enumerate(self.text_labels):
                similarity = float(similarities[i])
                if similarity >= self.similarity_threshold:
                    matches.append((label, similarity))
            
            if not matches:
                return None
            
            # Sort by confidence
            matches.sort(key=lambda x: x[1], reverse=True)
            
            # Create alert
            labels = [label for label, _ in matches]
            confidence = max(sim for _, sim in matches)
            
            # Determine category (simple heuristic - use first label's category)
            category = None
            if labels:
                # Could enhance this with category mapping
                category = labels[0]
            
            alert = Alert(
                timestamp_seconds=frame_data.timestamp_seconds,
                frame_number=frame_data.frame_number,
                labels=labels,
                confidence=float(confidence),
                category=category,
                metadata={
                    "all_similarities": {label: float(sim) for label, sim in zip(self.text_labels, similarities)}
                }
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            return None
    
    def _detection_loop(self):
        """Main detection loop running in background thread."""
        logger.info("Detection loop started")
        
        while self.is_running:
            try:
                # Get frame from queue (non-blocking)
                try:
                    frame_data = self.frame_queue.get(timeout=0.1)
                except Empty:
                    continue
                
                # Process frame
                alert = self._process_frame(frame_data)
                self.frames_processed += 1
                
                if alert:
                    self.alerts_emitted += 1
                    
                    # Emit alert to queue
                    if self.alert_queue:
                        try:
                            self.alert_queue.put_nowait(alert)
                        except:
                            logger.warning("Alert queue full, dropping alert")
                    
                    # Call callback if provided
                    if self.alert_callback:
                        try:
                            self.alert_callback(alert)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}", exc_info=True)
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}", exc_info=True)
                time.sleep(0.1)
        
        logger.info("Detection loop stopped")
    
    async def start(
        self,
        frame_queue: Queue,
        alert_queue: Optional[Queue] = None,
        alert_callback: Optional[Callable[[Alert], None]] = None
    ) -> bool:
        """
        Start detection engine.
        
        Args:
            frame_queue (Queue): Queue to read frames from
            alert_queue (Optional[Queue]): Queue to write alerts to
            alert_callback (Optional[Callable]): Callback function for alerts
            
        Returns:
            bool: True if started successfully
        """
        if self.is_running:
            logger.warning("LiveDetector is already running")
            return False
        
        # Prepare prompts
        await self._prepare_prompts()
        
        # Set queues and callback
        self.frame_queue = frame_queue
        self.alert_queue = alert_queue
        self.alert_callback = alert_callback
        
        # Reset statistics
        self.frames_processed = 0
        self.alerts_emitted = 0
        
        # Start detection thread
        self.is_running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        
        logger.info("LiveDetector started")
        return True
    
    def stop(self):
        """Stop detection engine."""
        if not self.is_running:
            return
        
        logger.info("Stopping LiveDetector...")
        self.is_running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        logger.info("LiveDetector stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "frames_processed": self.frames_processed,
            "alerts_emitted": self.alerts_emitted,
            "is_running": self.is_running
        }

