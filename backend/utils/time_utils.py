"""
Time utility functions for video analysis portion selection
"""

def parse_hms_to_seconds(hms: str) -> float:
    """
    Parse HH:MM:SS string to seconds.
    
    Args:
        hms: Time string in format "HH:MM:SS" or "MM:SS"
        
    Returns:
        Total seconds as float
        
    Raises:
        ValueError: If format is invalid
    """
    if not hms or not isinstance(hms, str):
        raise ValueError(f"Invalid time format: {hms}")
    
    parts = hms.split(':')
    if len(parts) == 2:
        # MM:SS format
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        # HH:MM:SS format
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    else:
        raise ValueError(f"Invalid time format: {hms}. Expected HH:MM:SS or MM:SS")

def seconds_to_hms(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS string.
    
    Args:
        seconds: Total seconds
        
    Returns:
        Time string in HH:MM:SS format
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def validate_time_window(start_ts: str, end_ts: str, video_duration: float) -> tuple[float, float]:
    """
    Validate and parse time window parameters.
    
    Args:
        start_ts: Start time string (HH:MM:SS)
        end_ts: End time string (HH:MM:SS)
        video_duration: Total video duration in seconds
        
    Returns:
        Tuple of (start_seconds, end_seconds)
        
    Raises:
        ValueError: If window is invalid
    """
    start_seconds = parse_hms_to_seconds(start_ts)
    end_seconds = parse_hms_to_seconds(end_ts)
    
    # Validate window
    if start_seconds < 0:
        raise ValueError(f"Start time cannot be negative: {start_ts}")
    if end_seconds > video_duration:
        raise ValueError(f"End time ({end_ts}) exceeds video duration ({seconds_to_hms(video_duration)})")
    if start_seconds >= end_seconds:
        raise ValueError(f"Start time ({start_ts}) must be before end time ({end_ts})")
    if end_seconds - start_seconds < 1:
        raise ValueError("Analysis window must be at least 1 second")
    
    return start_seconds, end_seconds
