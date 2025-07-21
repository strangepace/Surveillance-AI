# backend_v3/analyzer_simple.py
"""
Simplified analyzer pipeline for testing without PyTorch dependencies.
Demonstrates the full pipeline structure and integration.
"""
import os
import json
import hashlib
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import cv2

from .frame_extractor import extract_frames
from .prompt_interpreter import interpret_multiple_prompts
from .clip_generator import generate_preview_clip


@dataclass
class DetectionResult:
    """Structured detection result."""
    timestamp: str
    labels: List[str]
    confidence: float
    preview_clip: str
    summary: Optional[str] = None
    frame_index: Optional[int] = None
    prompt_matches: Optional[List[tuple]] = None


class SimpleVideoAnalyzer:
    """Simplified video analyzer for testing pipeline integration."""
    
    def __init__(self, config_path: str = "config/clip_config.yaml"):
        """
        Initialize the simplified video analyzer.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.similarity_threshold = 0.85
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Set similarity threshold from config
            if 'similarity_threshold' in self.config:
                self.similarity_threshold = self.config['similarity_threshold']
            
            print(f"✅ Loaded config: {self.config_path}")
            print(f"   Threshold: {self.similarity_threshold}")
            
        except Exception as e:
            print(f"⚠️  Config loading failed: {e}")
            # Use defaults
            self.config = {
                'model_name': 'ViT-B/32',
                'similarity_threshold': 0.85
            }
    
    def generate_video_id(self, video_path: str) -> str:
        """
        Generate a unique video ID based on file path and modification time.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Unique video ID
        """
        if not os.path.exists(video_path):
            return "unknown"
        
        # Get file stats
        stat = os.stat(video_path)
        file_info = f"{video_path}_{stat.st_mtime}_{stat.st_size}"
        
        # Generate hash
        video_id = hashlib.md5(file_info.encode()).hexdigest()[:8]
        return video_id
    
    def simulate_clip_similarity(self, frame_data: dict, text_labels: List[str]) -> List[tuple]:
        """
        Simulate CLIP similarity calculation for testing.
        
        Args:
            frame_data (dict): Frame information
            text_labels (List[str]): Text labels to compare against
            
        Returns:
            List[tuple]: Simulated similarity scores
        """
        import random
        
        # Simulate similarity scores based on frame content
        similarities = []
        
        for label in text_labels:
            # Simulate different similarity patterns
            if "man" in label.lower() or "person" in label.lower():
                # Higher chance of detecting people
                similarity = random.uniform(0.7, 0.95)
            elif "red" in label.lower() or "blue" in label.lower():
                # Medium chance for colors
                similarity = random.uniform(0.6, 0.9)
            elif "car" in label.lower() or "vehicle" in label.lower():
                # Lower chance for vehicles
                similarity = random.uniform(0.5, 0.8)
            else:
                # Random chance for other items
                similarity = random.uniform(0.3, 0.7)
            
            similarities.append((label, similarity))
        
        return similarities
    
    def analyze_video(self, video_path: str, prompts: List[str], output_dir: str) -> str:
        """
        Analyze video with given prompts and generate detection results.
        
        Args:
            video_path (str): Path to video file
            prompts (List[str]): List of natural language prompts
            output_dir (str): Directory to store results
            
        Returns:
            str: Path to results JSON file
        """
        print(f"🎬 Starting simplified video analysis: {video_path}")
        print(f"📝 Prompts: {prompts}")
        print(f"📁 Output directory: {output_dir}")
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        previews_dir = os.path.join(output_dir, "previews")
        os.makedirs(previews_dir, exist_ok=True)
        
        # Generate video ID
        video_id = self.generate_video_id(video_path)
        print(f"🆔 Video ID: {video_id}")
        
        # Step 1: Interpret prompts into structured categories
        print("\n🔍 Step 1: Interpreting prompts...")
        prompt_categories = interpret_multiple_prompts(prompts)
        
        # Flatten all detection labels
        all_labels = []
        for categories in prompt_categories:
            for category, items in categories.items():
                all_labels.extend(items)
        
        all_labels = list(set(all_labels))  # Remove duplicates
        print(f"   Extracted {len(all_labels)} unique labels: {all_labels}")
        
        # Step 2: Extract frames from video
        print("\n🎞️  Step 2: Extracting frames...")
        frames_metadata = extract_frames(video_path, output_dir)
        
        # Extract frames and timestamps from metadata
        frames = []
        timestamps = []
        for metadata in frames_metadata:
            # Load the frame image
            frame_path = metadata['frame_path']
            frame = cv2.imread(frame_path)
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                timestamps.append(int(metadata['timestamp_seconds']))
        
        print(f"   Extracted {len(frames)} frames")
        
        # Step 3: Simulate CLIP processing
        print("\n📝 Step 3: Simulating CLIP encoding...")
        print(f"   Would encode {len(all_labels)} text prompts")
        
        # Step 4: Process frames and simulate detection
        print("\n🖼️  Step 4: Processing frames...")
        detection_results = []
        
        # Sample some frames for detection (to avoid processing all frames)
        sample_indices = [0, len(frames)//4, len(frames)//2, 3*len(frames)//4, len(frames)-1]
        
        for i, frame_idx in enumerate(sample_indices):
            if frame_idx >= len(frames):
                continue
                
            frame = frames[frame_idx]
            timestamp = timestamps[frame_idx]
            
            print(f"   Processing frame {frame_idx + 1}/{len(frames)}")
            
            # Simulate CLIP similarity calculation
            similarities = self.simulate_clip_similarity(
                {'frame_index': frame_idx, 'timestamp': timestamp}, 
                all_labels
            )
            
            # Find matches above threshold
            matches = [(label, sim) for label, sim in similarities if sim >= self.similarity_threshold]
            
            if matches:
                # Sort by confidence
                matches.sort(key=lambda x: x[1], reverse=True)
                
                # Generate preview clip
                timestamp_str = f"{timestamp//3600:02d}:{(timestamp%3600)//60:02d}:{timestamp%60:02d}"
                preview_path = generate_preview_clip(
                    video_path, 
                    previews_dir, 
                    timestamp_str, 
                    clip_length=3
                )
                
                # Create detection result
                labels = [label for label, _ in matches]
                confidence = max(sim for _, sim in matches)
                
                result = DetectionResult(
                    timestamp=timestamp_str,
                    labels=labels,
                    confidence=confidence,
                    preview_clip=preview_path,
                    frame_index=frame_idx,
                    prompt_matches=matches
                )
                
                detection_results.append(result)
                
                print(f"      ✅ Simulated match at {timestamp_str}: {labels} (confidence: {confidence:.3f})")
        
        # Step 5: Save results to JSON
        print(f"\n💾 Step 5: Saving results...")
        results_file = os.path.join(output_dir, f"video_{video_id}.json")
        
        # Convert results to JSON-serializable format
        json_results = []
        for result in detection_results:
            json_result = asdict(result)
            # Convert tuples to lists for JSON serialization
            if 'prompt_matches' in json_result and json_result['prompt_matches']:
                json_result['prompt_matches'] = [
                    [label, float(sim)] for label, sim in json_result['prompt_matches']
                ]
            json_results.append(json_result)
        
        # Save to file
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"   Saved {len(detection_results)} detections to {results_file}")
        print(f"🎉 Analysis complete! Found {len(detection_results)} matches.")
        
        return results_file


# Convenience function for easy usage
def analyze_video_simple(video_path: str, prompts: List[str], output_dir: str = "results") -> str:
    """
    Convenience function to analyze a video using simplified pipeline.
    
    Args:
        video_path (str): Path to video file
        prompts (List[str]): List of natural language prompts
        output_dir (str): Directory to store results
        
    Returns:
        str: Path to results JSON file
    """
    analyzer = SimpleVideoAnalyzer()
    return analyzer.analyze_video(video_path, prompts, output_dir) 