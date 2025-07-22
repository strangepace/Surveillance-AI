# backend_v3/analyzer.py
"""
Full analyzer pipeline for backend-v3.
Integrates frame extraction, CLIP loading, prompt interpretation, detection, and preview generation.
"""
import os
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import torch
import numpy as np

from .clip_loader import get_clip_model
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
    prompt_matches: Optional[List[str]] = None


class VideoAnalyzer:
    """Main analyzer pipeline for video surveillance."""
    
    def __init__(self, config_path: str = "config/clip_config.yaml"):
        """
        Initialize the video analyzer.
        
        Args:
            config_path (str): Path to CLIP configuration file
        """
        self.config_path = config_path
        self.clip_model = None
        self.clip_processor = None
        self.device = None
        self.config = None
        self.similarity_threshold = 0.85
        
        self._load_config()
        self._load_clip_model()
    
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
            print(f"   Model: {self.config.get('model_name', 'ViT-B/32')}")
            print(f"   Threshold: {self.similarity_threshold}")
            
        except Exception as e:
            print(f"⚠️  Config loading failed: {e}")
            # Use defaults
            self.config = {
                'model_name': 'ViT-B/32',
                'similarity_threshold': 0.85
            }
    
    def _load_clip_model(self):
        """Load CLIP model and processor."""
        try:
            self.clip_model, self.clip_tokenizer, self.clip_preprocess = get_clip_model(
                config_path=self.config_path
            )
            self.device = next(self.clip_model.parameters()).device
            print(f"✅ CLIP model loaded on {self.device}")
            
        except Exception as e:
            print(f"❌ CLIP model loading failed: {e}")
            raise
    
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
    
    def calculate_similarity(self, image_features: torch.Tensor, text_features: torch.Tensor) -> float:
        """
        Calculate cosine similarity between image and text features.
        
        Args:
            image_features (torch.Tensor): CLIP image features
            text_features (torch.Tensor): CLIP text features
            
        Returns:
            float: Cosine similarity score
        """
        # Normalize features
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Calculate cosine similarity
        similarity = (image_features @ text_features.T).squeeze()
        
        return similarity.item()
    
    def encode_text_prompts(self, prompts: List[str]) -> torch.Tensor:
        """
        Encode text prompts using CLIP.
        
        Args:
            prompts (List[str]): List of text prompts
            
        Returns:
            torch.Tensor: CLIP text features
        """
        if not self.clip_tokenizer:
            raise RuntimeError("CLIP tokenizer not loaded")
        
        # Process text prompts
        text_tokens = self.clip_tokenizer(prompts).to(self.device)
        
        # Encode with CLIP
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
        
        return text_features
    
    def encode_frames(self, frames: List[np.ndarray]) -> torch.Tensor:
        """
        Encode video frames using CLIP.
        
        Args:
            frames (List[np.ndarray]): List of video frames
            
        Returns:
            torch.Tensor: CLIP image features
        """
        if not self.clip_preprocess:
            raise RuntimeError("CLIP preprocess not loaded")
        
        # Process frames
        from PIL import Image
        processed_frames = torch.stack([
            self.clip_preprocess(Image.fromarray(frame)) for frame in frames
        ]).to(self.device)
        
        # Encode with CLIP
        with torch.no_grad():
            image_features = self.clip_model.encode_image(processed_frames)
        
        return image_features
    
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
        print(f"🎬 Starting video analysis: {video_path}")
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
        frames_data = extract_frames(video_path)
        frames = frames_data['frames']
        timestamps = frames_data['timestamps']
        
        print(f"   Extracted {len(frames)} frames")
        
        # Step 3: Encode text prompts with CLIP
        print("\n📝 Step 3: Encoding text prompts...")
        text_features = self.encode_text_prompts(all_labels)
        print(f"   Encoded {len(all_labels)} text prompts")
        
        # Step 4: Process frames in batches
        print("\n🖼️  Step 4: Processing frames...")
        batch_size = 8  # Process frames in batches for efficiency
        detection_results = []
        
        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i:i + batch_size]
            batch_timestamps = timestamps[i:i + batch_size]
            
            print(f"   Processing batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
            
            # Encode batch of frames
            image_features = self.encode_frames(batch_frames)
            
            # Compare each frame with each text prompt
            for j, (frame, timestamp) in enumerate(zip(batch_frames, batch_timestamps)):
                frame_idx = i + j
                
                # Calculate similarities for this frame
                frame_features = image_features[j:j+1]
                similarities = []
                
                for k, label in enumerate(all_labels):
                    text_feature = text_features[k:k+1]
                    similarity = self.calculate_similarity(frame_features, text_feature)
                    similarities.append((label, similarity))
                
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
                    
                    print(f"      ✅ Match at {timestamp_str}: {labels} (confidence: {confidence:.3f})")
        
        # Step 5: Save results to JSON
        print(f"\n💾 Step 5: Saving results...")
        results_file = os.path.join(output_dir, f"video_{video_id}.json")
        
        # Convert results to JSON-serializable format
        json_results = []
        for result in detection_results:
            json_result = asdict(result)
            # Convert torch tensors to lists if present
            if 'prompt_matches' in json_result and json_result['prompt_matches']:
                json_result['prompt_matches'] = [
                    (label, float(sim)) for label, sim in json_result['prompt_matches']
                ]
            json_results.append(json_result)
        
        # Save to file
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"   Saved {len(detection_results)} detections to {results_file}")
        print(f"🎉 Analysis complete! Found {len(detection_results)} matches.")
        
        return results_file
    
    def analyze_video_simple(self, video_path: str, prompts: List[str], output_dir: str) -> str:
        """
        Simplified analysis for testing without full pipeline.
        
        Args:
            video_path (str): Path to video file
            prompts (List[str]): List of natural language prompts
            output_dir (str): Directory to store results
            
        Returns:
            str: Path to results JSON file
        """
        print(f"🎬 Simple video analysis: {video_path}")
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        previews_dir = os.path.join(output_dir, "previews")
        os.makedirs(previews_dir, exist_ok=True)
        
        # Generate video ID
        video_id = self.generate_video_id(video_path)
        
        # Simulate some detections for testing
        detection_results = []
        
        # Sample detections at different timestamps
        sample_timestamps = ["00:00:30", "00:01:15", "00:01:45"]
        sample_labels = [
            ["man", "red shirt"],
            ["car", "blue"],
            ["person", "walking"]
        ]
        sample_confidences = [0.92, 0.88, 0.85]
        
        for i, (timestamp, labels, confidence) in enumerate(zip(sample_timestamps, sample_labels, sample_confidences)):
            try:
                # Generate preview clip
                preview_path = generate_preview_clip(
                    video_path, 
                    previews_dir, 
                    timestamp, 
                    clip_length=3
                )
                
                result = DetectionResult(
                    timestamp=timestamp,
                    labels=labels,
                    confidence=confidence,
                    preview_clip=preview_path
                )
                
                detection_results.append(result)
                print(f"   ✅ Simulated detection at {timestamp}: {labels} (confidence: {confidence:.3f})")
                
            except Exception as e:
                print(f"   ⚠️  Failed to generate preview for {timestamp}: {e}")
        
        # Save results
        results_file = os.path.join(output_dir, f"video_{video_id}.json")
        
        json_results = [asdict(result) for result in detection_results]
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"💾 Saved {len(detection_results)} detections to {results_file}")
        return results_file


# Convenience function for easy usage
def analyze_video(video_path: str, prompts: List[str], output_dir: str = "results") -> tuple:
    """
    Convenience function to analyze a video.
    Args:
        video_path (str): Path to video file
        prompts (List[str]): List of natural language prompts
        output_dir (str): Directory to store results
    Returns:
        tuple: (results: list, json_path: str)
    """
    analyzer = VideoAnalyzer()
    results_file = analyzer.analyze_video(video_path, prompts, output_dir)
    # Load results from file
    with open(results_file, 'r') as f:
        results = json.load(f)
    return results, results_file 