from typing import List, Dict, Any
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=int(seconds)))

async def match_events(search_terms: List[str], video_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Match search terms with video analysis results.
    Returns a list of matched events with timestamps.
    """
    try:
        matches = []
        match_index = 1
        
        # Combine labels and objects for matching
        all_detections = video_analysis["labels"] + video_analysis["objects"]
        
        # Convert search terms to lowercase for case-insensitive matching
        search_terms = [term.lower() for term in search_terms]
        
        for detection in all_detections:
            # Convert detection label to lowercase for matching
            detection_label = detection["label"].lower()
            
            # Check if any search term matches the detection label
            for term in search_terms:
                if term in detection_label:
                    match = {
                        "match_id": f"match_{match_index:03d}",
                        "label": detection["label"],
                        "confidence": round(detection["confidence"], 2),
                        "start_time": format_timestamp(detection["start_time"]),
                        "end_time": format_timestamp(detection["end_time"])
                    }
                    matches.append(match)
                    match_index += 1
                    break  # Break after first match to avoid duplicates
        
        # Sort matches by start time
        matches.sort(key=lambda x: x["start_time"])
        
        return matches
        
    except Exception as e:
        logger.error(f"Error matching events: {str(e)}")
        raise Exception(f"Failed to match events: {str(e)}") 