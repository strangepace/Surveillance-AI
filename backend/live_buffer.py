"""
Live Storage Buffer - In-memory buffer for recent alerts.

Stores the last N minutes of alerts per stream for history, scrubbing, and replay.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime, timedelta
import threading

from live_detector import Alert

logger = logging.getLogger("live_buffer")


@dataclass
class BufferedAlert:
    """Alert stored in buffer with metadata."""
    alert: Alert
    received_at: float  # Unix timestamp when alert was received
    stream_id: str  # Stream identifier
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        alert_dict = self.alert.to_dict()
        return {
            **alert_dict,
            "received_at": self.received_at,
            "stream_id": self.stream_id,
            # Add frontend-compatible fields
            "alertId": f"live_{self.alert.frame_number}_{int(self.alert.timestamp_seconds)}",
            "cameraId": self.stream_id,
            "tsUnix": int(self.received_at),
            "timestamp": self._format_timestamp(self.alert.timestamp_seconds),
            "frame_index": self.alert.frame_number,
            "category": self.alert.category or (self.alert.labels[0] if self.alert.labels else "activity"),
        }
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format relative timestamp as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class LiveBuffer:
    """
    In-memory buffer for live alerts.
    
    Stores alerts per stream with automatic cleanup of old entries.
    """
    
    def __init__(self, buffer_window_sec: float = 600.0):
        """
        Initialize live buffer.
        
        Args:
            buffer_window_sec (float): How many seconds of alerts to keep (default: 600 = 10 minutes)
        """
        self.buffer_window_sec = buffer_window_sec
        self.retention_seconds = buffer_window_sec
        
        # Storage: stream_id -> list of BufferedAlert (ordered by timestamp)
        self._alerts: Dict[str, List[BufferedAlert]] = defaultdict(list)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self._total_alerts_stored = 0
        self._total_alerts_cleaned = 0
        
        logger.info(f"LiveBuffer initialized: buffer_window={buffer_window_sec} seconds ({buffer_window_sec/60:.1f} minutes)")
    
    def add_alert(self, alert: Alert, stream_id: str = "default"):
        """
        Add an alert to the buffer.
        
        Args:
            alert: Alert to store
            stream_id: Stream identifier (default: "default")
        """
        with self._lock:
            received_at = time.time()
            buffered = BufferedAlert(
                alert=alert,
                received_at=received_at,
                stream_id=stream_id
            )
            
            self._alerts[stream_id].append(buffered)
            self._total_alerts_stored += 1
            
            # Cleanup old alerts for this stream
            self._cleanup_stream(stream_id)
    
    def get_recent_alerts(
        self,
        stream_id: str = "default",
        window_sec: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent alerts from buffer within time window.
        
        Args:
            stream_id: Stream identifier (default: "default")
            window_sec: Time window in seconds (None = use buffer_window_sec)
            limit: Maximum number of alerts to return (None = all)
            
        Returns:
            List of alert dictionaries, ordered by timestamp ascending (oldest → newest)
        """
        with self._lock:
            if stream_id not in self._alerts:
                return []
            
            alerts = self._alerts[stream_id]
            
            # Use specified window or default buffer window
            window = window_sec if window_sec is not None else self.buffer_window_sec
            cutoff_time = time.time() - window
            
            # Filter by time window
            alerts = [a for a in alerts if a.received_at >= cutoff_time]
            
            # Sort by timestamp ascending (oldest → newest) as per requirements
            alerts = sorted(alerts, key=lambda a: a.alert.timestamp_seconds, reverse=False)
            
            # Apply limit
            if limit is not None:
                alerts = alerts[:limit]
            
            # Convert to dictionaries
            return [a.to_dict() for a in alerts]
    
    def get_alerts_in_range(
        self,
        stream_id: str = "default",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get alerts within a time range.
        
        Args:
            stream_id: Stream identifier
            start_time: Start timestamp (Unix seconds, None = beginning)
            end_time: End timestamp (Unix seconds, None = now)
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert dictionaries
        """
        with self._lock:
            if stream_id not in self._alerts:
                return []
            
            alerts = self._alerts[stream_id]
            
            # Filter by time range
            if start_time is not None or end_time is not None:
                filtered = []
                for alert in alerts:
                    alert_time = alert.received_at
                    if start_time is not None and alert_time < start_time:
                        continue
                    if end_time is not None and alert_time > end_time:
                        continue
                    filtered.append(alert)
                alerts = filtered
            
            # Sort by timestamp (newest first)
            alerts = sorted(alerts, key=lambda a: a.alert.timestamp_seconds, reverse=True)
            
            # Apply limit
            if limit is not None:
                alerts = alerts[:limit]
            
            return [a.to_dict() for a in alerts]
    
    def get_streams(self) -> List[str]:
        """Get list of active stream IDs."""
        with self._lock:
            return list(self._alerts.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        with self._lock:
            total_alerts = sum(len(alerts) for alerts in self._alerts.values())
            return {
                "buffer_window_sec": self.buffer_window_sec,
                "buffer_window_minutes": self.buffer_window_sec / 60.0,
                "streams": len(self._alerts),
                "total_alerts": total_alerts,
                "alerts_per_stream": {sid: len(alerts) for sid, alerts in self._alerts.items()},
                "total_stored": self._total_alerts_stored,
                "total_cleaned": self._total_alerts_cleaned
            }
    
    def _cleanup_stream(self, stream_id: str):
        """Clean up old alerts for a specific stream."""
        if stream_id not in self._alerts:
            return
        
        cutoff_time = time.time() - self.retention_seconds
        alerts = self._alerts[stream_id]
        
        # Remove alerts older than retention period
        initial_count = len(alerts)
        self._alerts[stream_id] = [
            a for a in alerts if a.received_at >= cutoff_time
        ]
        removed_count = initial_count - len(self._alerts[stream_id])
        
        if removed_count > 0:
            self._total_alerts_cleaned += removed_count
            logger.debug(f"Cleaned {removed_count} old alerts from stream '{stream_id}'")
    
    def cleanup_all(self):
        """Clean up old alerts from all streams."""
        with self._lock:
            for stream_id in list(self._alerts.keys()):
                self._cleanup_stream(stream_id)
    
    def clear_stream(self, stream_id: str):
        """Clear all alerts for a specific stream."""
        with self._lock:
            if stream_id in self._alerts:
                count = len(self._alerts[stream_id])
                del self._alerts[stream_id]
                logger.info(f"Cleared {count} alerts from stream '{stream_id}'")
    
    def clear_all(self):
        """Clear all alerts from all streams."""
        with self._lock:
            total = sum(len(alerts) for alerts in self._alerts.values())
            self._alerts.clear()
            logger.info(f"Cleared all {total} alerts from buffer")


# Global buffer instance
_live_buffer: Optional[LiveBuffer] = None


def initialize_buffer(buffer_window_sec: float = 600.0) -> LiveBuffer:
    """
    Initialize the global live buffer.
    
    Args:
        buffer_window_sec: How many seconds of alerts to keep (default: 600 = 10 minutes)
        
    Returns:
        LiveBuffer instance
    """
    global _live_buffer
    _live_buffer = LiveBuffer(buffer_window_sec=buffer_window_sec)
    logger.info(f"Live buffer initialized with {buffer_window_sec} seconds ({buffer_window_sec/60:.1f} minutes) retention")
    return _live_buffer


def get_buffer() -> LiveBuffer:
    """
    Get the global live buffer instance.
    
    Returns:
        LiveBuffer instance
        
    Raises:
        RuntimeError: If buffer not initialized
    """
    if _live_buffer is None:
        raise RuntimeError("Live buffer not initialized. Call initialize_buffer() first.")
    return _live_buffer


def is_initialized() -> bool:
    """Check if buffer is initialized."""
    return _live_buffer is not None

