"""
Central Alert Queue for Live Stream Processing.

This module provides a shared alert queue that can be consumed by:
- Task 7: WebSocket broadcast
- Task 8: Live buffer storage
- Any other downstream consumers
"""

import logging
from typing import Optional, List
from queue import Queue, Empty
from dataclasses import asdict
from live_detector import Alert

logger = logging.getLogger("live_alerts_queue")

# Global alert queue instance
_live_alerts_queue: Optional[Queue] = None
_queue_maxsize: int = 1000


def initialize_queue(maxsize: int = 1000):
    """
    Initialize the global alert queue.
    
    Args:
        maxsize (int): Maximum queue size (default: 1000)
    """
    global _live_alerts_queue, _queue_maxsize
    _live_alerts_queue = Queue(maxsize=maxsize)
    _queue_maxsize = maxsize
    logger.info(f"Live alerts queue initialized with maxsize={maxsize}")


def get_queue() -> Queue:
    """
    Get the global alert queue instance.
    
    Returns:
        Queue: The global alert queue
        
    Raises:
        RuntimeError: If queue not initialized
    """
    if _live_alerts_queue is None:
        raise RuntimeError("Live alerts queue not initialized. Call initialize_queue() first.")
    return _live_alerts_queue


def push_alert(alert: Alert):
    """
    Push an alert into the queue.
    
    Args:
        alert (Alert): Alert to push
    """
    queue = get_queue()
    try:
        queue.put_nowait(alert)
    except:
        # Queue full - log warning and drop alert
        logger.warning(f"Alert queue full, dropping alert: {alert.labels} @ {alert.timestamp_seconds:.2f}s")


def get_alert(timeout: Optional[float] = None) -> Optional[Alert]:
    """
    Get next alert from queue.
    
    Args:
        timeout (Optional[float]): Timeout in seconds (None = blocking)
        
    Returns:
        Optional[Alert]: Alert or None if timeout/empty
    """
    queue = get_queue()
    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None


def get_all_alerts(max_count: Optional[int] = None) -> List[Alert]:
    """
    Get all available alerts from queue (non-blocking).
    
    Args:
        max_count (Optional[int]): Maximum number of alerts to retrieve
        
    Returns:
        List[Alert]: List of alerts
    """
    queue = get_queue()
    alerts = []
    count = 0
    
    while True:
        if max_count and count >= max_count:
            break
        
        try:
            alert = queue.get_nowait()
            alerts.append(alert)
            count += 1
        except Empty:
            break
    
    return alerts


def get_queue_size() -> int:
    """
    Get current queue size.
    
    Returns:
        int: Number of alerts in queue
    """
    if _live_alerts_queue is None:
        return 0
    return _live_alerts_queue.qsize()


def is_initialized() -> bool:
    """
    Check if queue is initialized.
    
    Returns:
        bool: True if initialized
    """
    return _live_alerts_queue is not None


def clear_queue():
    """Clear all alerts from queue."""
    if _live_alerts_queue is None:
        return
    
    while True:
        try:
            _live_alerts_queue.get_nowait()
        except Empty:
            break
    
    logger.info("Live alerts queue cleared")

