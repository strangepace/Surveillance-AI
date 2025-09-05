# backend_v3/analyzer.py
"""
Full analyzer pipeline for backend.
Integrates frame extraction, CLIP loading, prompt interpretation, detection, and preview generation.
Enhanced with error handling and Colab compatibility.
"""
import os
import json
import hashlib
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import torch
import numpy as np
import shutil
import cv2

# Import our new modules
from error_handler import error_handler, ErrorType
from colab_compat import colab_compat

from clip_loader import get_clip_model
from frame_extractor import extract_frames
from prompt_interpreter import interpret_multiple_prompts
from clip_generator import generate_preview_clip
from alert_classifier import classify_detections, get_alert_summary

# Set up logging
logger = logging.getLogger("analyzer")


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
        
        # Initialize with error handling
        try:
            self._load_config()
            self._load_clip_model()
        except Exception as e:
            error_handler.log_error(e, ErrorType.CLIP_MODEL, {"config_path": config_path})
            raise
    
    def _load_config(self):
        """Load configuration from YAML file with error handling."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Set similarity threshold from config
            if 'similarity_threshold' in self.config:
                self.similarity_threshold = self.config['similarity_threshold']
            
            print(f"Loaded config: {self.config_path}")
            print(f"   Model: {self.config.get('model_name', 'ViT-B-32')}")
            print(f"   Threshold: {self.similarity_threshold}")
            
        except FileNotFoundError as e:
            error_msg = f"Configuration file not found: {self.config_path}"
            error_handler.log_error(e, ErrorType.FILE_IO, {"config_path": self.config_path})
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            error_handler.log_error(e, ErrorType.FILE_IO, {"config_path": self.config_path})
            raise Exception(error_msg)
    
    def _load_clip_model(self):
        """Load CLIP model and processor with error handling."""
        try:
            self.clip_model, self.clip_tokenizer, self.clip_preprocess, self.device = get_clip_model(
                config_path=self.config_path
            )
            print(f"CLIP model loaded on {self.device}")
            
        except Exception as e:
            error_msg = f"CLIP model loading failed: {e}"
            error_handler.log_error(e, ErrorType.CLIP_MODEL, {"config_path": self.config_path})
            raise Exception(error_msg)
    
    def generate_video_id(self, video_path: str) -> str:
        """
        Generate a unique video ID based on file path and modification time.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Unique video ID
        """
        try:
            # Get file stats
            stat = os.stat(video_path)
            file_info = f"{video_path}_{stat.st_mtime}_{stat.st_size}"
            
            # Generate hash
            video_id = hashlib.md5(file_info.encode()).hexdigest()[:8]
            return video_id
            
        except Exception as e:
            error_handler.log_error(e, ErrorType.FILE_IO, {"video_path": video_path})
            # Fallback to timestamp-based ID
            return f"video_{int(time.time())}"
    
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
        
        # Process text prompts and move to device
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
        
        # Process frames and move to device
        from PIL import Image
        processed_frames = torch.stack([
            self.clip_preprocess(Image.fromarray(frame)) for frame in frames
        ]).to(self.device)
        
        # Encode with CLIP
        with torch.no_grad():
            image_features = self.clip_model.encode_image(processed_frames)
        
        return image_features
    
    async def analyze_video(self, video_path: str, prompts: List[str], output_dir: str) -> str:
        """
        Analyze video with given prompts and generate detection results.
        
        Args:
            video_path (str): Path to video file
            prompts (List[str]): List of natural language prompts
            output_dir (str): Directory to store results
            
        Returns:
            str: Path to results JSON file
        """
        logger.info(f"Starting video analysis: {video_path}")
        logger.info(f"Prompts: {prompts}")
        logger.info(f"Output directory: {output_dir}")
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        previews_dir = os.path.join(output_dir, "previews")
        os.makedirs(previews_dir, exist_ok=True)
        
        # Generate video ID
        video_id = self.generate_video_id(video_path)
        logger.info(f"Video ID: {video_id}")

        # Prepare temp frame directory
        temp_frame_dir = os.path.join("temp_frames", video_id)
        os.makedirs(temp_frame_dir, exist_ok=True)

        try:
            # Step 1: Interpret prompts into structured categories
            logger.info("\nStep 1: Interpreting prompts...")
            prompt_categories = await interpret_multiple_prompts(prompts)
            
            # Extract meaningful labels from prompts
            all_labels = []
            for category_info in prompt_categories:
                # Extract labels from the new structure
                labels = category_info.get("labels", [])
                if labels:
                    all_labels.extend(labels)
                else:
                    # Fallback: use the original prompt
                    prompt = category_info.get("prompt", "")
                    all_labels.append(prompt)
            
            all_labels = list(set(all_labels))  # Remove duplicates
            logger.info(f"   Extracted {len(all_labels)} unique labels: {all_labels}")

            # Step 2: Extract frames from video
            logger.info("\nStep 2: Extracting frames...")
            # DIAGNOSTIC: Use sampling rate from config
            sampling_rate = self.config.get('frame_extraction', {}).get('sampling_rate', 5)
            frames_data = extract_frames(video_path, temp_frame_dir, sampling_rate=sampling_rate)
            # frames_data is a list of dicts with keys: frame_path, timestamp, timestamp_seconds, frame_number
            frames = [cv2.imread(fd['frame_path']) for fd in frames_data]
            timestamps = [fd['timestamp_seconds'] for fd in frames_data]
            logger.info(f"   Extracted {len(frames)} frames")

            # Step 3: Encode text prompts with CLIP
            logger.info("\nStep 3: Encoding text prompts...")
            text_features = self.encode_text_prompts(all_labels)
            logger.info(f"   Encoded {len(all_labels)} text prompts")

            # Step 4: Process frames in batches
            logger.info("\nStep 4: Processing frames...")
            batch_size = 8  # Process frames in batches for efficiency
            detection_results = []
            
            # DIAGNOSTIC: Track similarity statistics
            all_similarities = []
            frames_processed = 0
            
            for i in range(0, len(frames), batch_size):
                batch_frames = frames[i:i + batch_size]
                batch_timestamps = timestamps[i:i + batch_size]
                logger.info(f"   Processing batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
                # Encode batch of frames
                image_features = self.encode_frames(batch_frames)
                # Compare each frame with each text prompt
                for j, (frame, timestamp) in enumerate(zip(batch_frames, batch_timestamps)):
                    frame_idx = i + j
                    frames_processed += 1
                    
                    # Calculate similarities for this frame
                    frame_features = image_features[j:j+1]
                    similarities = []
                    
                    for k, label in enumerate(all_labels):
                        text_feature = text_features[k:k+1]
                        similarity = self.calculate_similarity(frame_features, text_feature)
                        similarities.append((label, similarity))
                        all_similarities.append(similarity)  # DIAGNOSTIC: collect all similarities
                    
                    # DIAGNOSTIC: Log every ~30 frames
                    if frames_processed % 30 == 0:
                        top_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
                        logger.debug(f"frame={frame_idx} ts={timestamp:.1f}s top3={top_similarities}")
                    
                    # Find matches above threshold
                    matches = [(label, sim) for label, sim in similarities if sim >= self.similarity_threshold]
                    
                    if matches:
                        # Sort by confidence
                        matches.sort(key=lambda x: x[1], reverse=True)
                        
                        # Generate preview clip
                        timestamp_str = f"{int(timestamp//3600):02d}:{int((timestamp%3600)//60):02d}:{int(timestamp%60):02d}"
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
                        
                        logger.info(f"✅ Match at {timestamp_str}: {labels} (confidence: {confidence:.3f})")
            
            # Step 5: Save results to JSON
            logger.info(f"\nStep 5: Saving results...")
            
            # Step 5.1: Classify detections into alert categories
            logger.info(f"Step 5.1: Classifying alerts...")
            
            # Convert DetectionResult objects to dictionaries for alert classifier
            detection_dicts = []
            for result in detection_results:
                detection_dict = {
                    "timestamp": result.timestamp,
                    "labels": result.labels,
                    "confidence": result.confidence,
                    "preview_clip": result.preview_clip,
                    "summary": result.summary,
                    "frame_index": result.frame_index,
                    "prompt_matches": result.prompt_matches
                }
                detection_dicts.append(detection_dict)
            
            classified_detections = classify_detections(detection_dicts)
            alert_summary = get_alert_summary(classified_detections)
            
            logger.info(f"📊 Alert Summary:")
            logger.info(f"   Total detections: {alert_summary['total_detections']}")
            logger.info(f"   Categories: {alert_summary['categories']}")
            logger.info(f"   Priorities: {alert_summary['priorities']}")
            
            # Save JSON results in organized directory
            json_dir = os.path.join(output_dir, "json")
            os.makedirs(json_dir, exist_ok=True)
            results_file = os.path.join(json_dir, f"video_{video_id}.json")
            
            # Convert results to JSON-serializable format
            json_results = []
            for result in classified_detections:
                # result is already a dictionary from alert classifier
                json_result = result.copy()
                # Convert torch tensors to lists if present
                if 'prompt_matches' in json_result and json_result['prompt_matches']:
                    json_result['prompt_matches'] = [
                        (label, float(sim)) for label, sim in json_result['prompt_matches']
                    ]
                json_results.append(json_result)
            
            # Add alert summary to results
            final_results = {
                "detections": json_results,
                "alert_summary": alert_summary,
                "video_id": video_id,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save to file
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2)
            
            logger.info(f"Saved {len(classified_detections)} detections to {results_file}")
            logger.info(f"🎉 Analysis complete! Found {len(classified_detections)} matches.")
            
            # DIAGNOSTIC: Log similarity statistics summary
            if all_similarities:
                sim_min = min(all_similarities)
                sim_max = max(all_similarities)
                sim_mean = sum(all_similarities) / len(all_similarities)
                logger.debug(f"frames_processed={frames_processed} detections_total={len(classified_detections)} sim_min={sim_min:.3f} sim_mean={sim_mean:.3f} sim_max={sim_max:.3f}")
            
            return results_file
        finally:
            # Clean up temp frame directory
            if os.path.exists(temp_frame_dir):
                shutil.rmtree(temp_frame_dir)
    
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
        print(f"Simple video analysis: {video_path}")
        
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
        
        # Save results in organized directory
        json_dir = os.path.join(output_dir, "json")
        os.makedirs(json_dir, exist_ok=True)
        results_file = os.path.join(json_dir, f"video_{video_id}.json")
        
        json_results = [asdict(result) for result in detection_results]
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"💾 Saved {len(detection_results)} detections to {results_file}")
        return results_file


# Convenience function for easy usage
async def analyze_video(video_path: str, prompts: List[str], output_dir: str = "results") -> tuple:
    """
    Main analysis function with comprehensive error handling.
    
    Args:
        video_path (str): Path to video file
        prompts (List[str]): List of prompts to search for
        output_dir (str): Directory to save results
        
    Returns:
        tuple: (results_dict, json_path)
    """
    logger = logging.getLogger("analyzer")
    logger.debug("DEBUG: Entered analyze_video function")
    
    try:
        # Validate inputs
        if not video_path or not os.path.exists(video_path):
            raise Exception(f"Video file not found: {video_path}")
        
        if not prompts or len(prompts) == 0:
            raise Exception("No prompts provided")
        
        # Use Colab-compatible output directory
        if colab_compat.is_colab():
            output_dir = colab_compat.get_results_dir()
            print(f"🌐 Using Colab output directory: {output_dir}")
        
        # Ensure output directory exists
        colab_compat.ensure_directory(output_dir)
        
        # Initialize analyzer with error handling
        try:
            analyzer = VideoAnalyzer()
        except Exception as e:
            error_handler.log_error(e, ErrorType.CLIP_MODEL, {
                "video_path": video_path,
                "prompts": prompts
            })
            raise Exception(f"Failed to initialize analyzer: {e}")
        
        # Run analysis
        try:
            results_file = await analyzer.analyze_video(video_path, prompts, output_dir)
        except Exception as e:
            error_handler.log_error(e, ErrorType.FRAME_EXTRACTION, {
                "video_path": video_path,
                "prompts": prompts,
                "output_dir": output_dir
            })
            raise Exception(f"Analysis failed: {e}")
        
        # Load results from file with error handling
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except Exception as e:
            error_handler.log_error(e, ErrorType.FILE_IO, {
                "results_file": results_file,
                "operation": "read_results"
            })
            raise Exception(f"Failed to read results: {e}")
        
        print("DEBUG - Results Type:", type(results))
        print("DEBUG - Sample Result:", results[:1] if isinstance(results, list) else results)
        print("DEBUG: About to return from analyze_video")
        
        return results, results_file
        
    except Exception as e:
        # Log the error and re-raise
        error_handler.log_error(e, ErrorType.UNKNOWN, {
            "video_path": video_path,
            "prompts": prompts,
            "output_dir": output_dir
        })
        raise 
