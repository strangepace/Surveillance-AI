# backend_v3/engine.py

import os
import json
from typing import List, Dict, Any
from config import CONFIDENCE_THRESHOLDS, PREVIEW_CLIP_DURATION, PREVIEW_CLIP_DIR, OUTPUT_JSON_DIR
from detectors import PeopleDetector, ColorDetector, FireDetector

class DetectionEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.people_detector = PeopleDetector(self.config)
        self.color_detector = ColorDetector(self.config)
        self.fire_detector = FireDetector(self.config)
        # TODO: Add other detectors as needed

    def analyze_video(self, video_path: str, prompt: str) -> List[Dict[str, Any]]:
        """Run all detectors and aggregate results for the video."""
        results = []
        # Run detectors (expand as needed)
        people_results = self.people_detector.detect(video_path)
        color_results = self.color_detector.detect(video_path)
        fire_results = self.fire_detector.detect(video_path)
        # TODO: Merge and deduplicate results, match to prompt
        # For now, just concatenate
        all_results = people_results + color_results + fire_results
        for idx, event in enumerate(all_results):
            # Generate preview clip (placeholder)
            preview_clip_path = self.generate_preview_clip(video_path, event['timestamp'], idx)
            # Build event object
            results.append({
                'timestamp': event['timestamp'],
                'labels': event['labels'],
                'confidence': event['confidence'],
                'preview_clip': preview_clip_path,
                'summary': None  # Placeholder for future natural-language summary
            })
        return results

    def generate_preview_clip(self, video_path: str, timestamp: str, idx: int) -> str:
        """Generate a short video clip around the event timestamp (placeholder)."""
        # TODO: Implement actual video clip extraction
        # For now, just return a placeholder path
        filename = f"clip_{idx:03d}.mp4"
        return os.path.join(PREVIEW_CLIP_DIR, filename)

    def save_results(self, video_path: str, results: List[Dict[str, Any]]):
        """Save results to a JSON file in the output directory."""
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(OUTPUT_JSON_DIR, f"{video_name}_analysis.json")
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}") 