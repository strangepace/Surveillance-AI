"""
Analyzer Service - Orchestration layer for video analysis pipeline.

This module encapsulates the main analysis workflow:
- Media loading and validation
- Frame extraction
- CLIP embedding computation
- Detector execution
- FAISS build/load decision
- Result assembly

Separates orchestration logic from low-level helpers and API concerns.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import torch
import numpy as np
import cv2
import shutil

from error_handler import error_handler, ErrorType
from colab_compat import colab_compat
from clip_loader import get_clip_model
from frame_extractor import extract_frames
from prompt_interpreter import interpret_multiple_prompts
from clip_generator import generate_preview_clip
from alert_classifier import classify_detections, get_alert_summary
from faiss_indexer import FAISSIndexer
from config_loader import load_clip_config

logger = logging.getLogger("analyzer_service")


@dataclass
class DetectionResult:
    """Structured detection result."""
    timestamp: str
    labels: List[str]
    confidence: float
    preview_clip: str
    summary: Optional[str] = None
    frame_index: Optional[int] = None
    prompt_matches: Optional[List[Tuple[str, float]]] = None


class AnalyzerService:
    """
    Main orchestration service for video analysis.
    
    Encapsulates the complete analysis pipeline:
    - Prompt interpretation
    - Frame extraction
    - CLIP encoding
    - Detection matching
    - FAISS indexing
    - Result classification and saving
    """
    
    def __init__(self, config_path: str = "config/clip_config.yaml"):
        """
        Initialize the analyzer service.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.clip_model = None
        self.clip_tokenizer = None
        self.clip_preprocess = None
        self.device = None
        self.similarity_threshold = 0.21  # Default, will be overridden by config
        
        self._load_config()
        self._load_clip_model()
    
    def _load_config(self):
        """Load configuration from YAML file with backward compatibility."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Set similarity threshold from config (support both old and new structure)
            if 'detection' in self.config and 'similarity_threshold' in self.config['detection']:
                self.similarity_threshold = self.config['detection']['similarity_threshold']
            elif 'similarity_threshold' in self.config:  # Legacy support
                self.similarity_threshold = self.config['similarity_threshold']
            
            # Get model name (support both old and new structure)
            model_name = "ViT-B-32"
            if 'model' in self.config and 'name' in self.config['model']:
                model_name = self.config['model']['name']
            elif 'model_name' in self.config:  # Legacy support
                model_name = self.config['model_name']
            
            logger.info(f"Loaded config: {self.config_path}")
            logger.info(f"   Model: {model_name}")
            logger.info(f"   Threshold: {self.similarity_threshold}")
            
        except FileNotFoundError as e:
            error_msg = f"Configuration file not found: {self.config_path}"
            error_handler.log_error(e, ErrorType.FILE_IO, {"config_path": self.config_path})
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            error_handler.log_error(e, ErrorType.FILE_IO, {"config_path": self.config_path})
            raise Exception(error_msg)
    
    def _load_clip_model(self):
        """Load CLIP model and processor."""
        try:
            self.clip_model, self.clip_tokenizer, self.clip_preprocess, self.device = get_clip_model(
                config_path=self.config_path
            )
            logger.info(f"CLIP model loaded on {self.device}")
        except Exception as e:
            error_msg = f"CLIP model loading failed: {e}"
            error_handler.log_error(e, ErrorType.CLIP_MODEL, {"config_path": self.config_path})
            raise Exception(error_msg)
    
    def generate_video_id(self, video_path: str) -> str:
        """
        Generate a unique video ID from file path.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Unique video ID
        """
        try:
            import hashlib
            stat = os.stat(video_path)
            file_info = f"{video_path}_{stat.st_mtime}_{stat.st_size}"
            video_id = hashlib.md5(file_info.encode()).hexdigest()[:8]
            return f"video_{video_id}"
        except Exception as e:
            error_handler.log_error(e, ErrorType.FILE_IO, {"video_path": video_path})
            # Fallback to timestamp-based ID
            return f"video_{int(time.time())}"
    
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
        
        text_tokens = self.clip_tokenizer(prompts).to(self.device)
        
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
        
        from PIL import Image
        processed_frames = torch.stack([
            self.clip_preprocess(Image.fromarray(frame)) for frame in frames
        ]).to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.encode_image(processed_frames)
        
        return image_features
    
    def calculate_similarity(self, image_features: torch.Tensor, text_features: torch.Tensor) -> float:
        """
        Calculate cosine similarity between image and text features.
        
        Args:
            image_features (torch.Tensor): CLIP image features
            text_features (torch.Tensor): CLIP text features
            
        Returns:
            float: Cosine similarity score
        """
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        similarity = (image_features @ text_features.T).squeeze()
        return similarity.item()
    
    async def analyze_video(
        self, 
        video_path: str, 
        prompts: List[str], 
        output_dir: str, 
        media_id: Optional[str] = None
    ) -> str:
        """
        Analyze video with given prompts and generate detection results.
        Supports cached re-analysis if FAISS index exists.
        
        Args:
            video_path (str): Path to video file
            prompts (List[str]): List of natural language prompts
            output_dir (str): Directory to store results
            media_id (Optional[str]): Media ID for cached re-analysis. If None, generates from path.
            
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
        
        # Use provided media_id or generate from path
        if media_id:
            video_id = media_id
            logger.info(f"Using provided media_id: {video_id}")
        else:
            video_id = self.generate_video_id(video_path)
            logger.info(f"Generated video ID: {video_id}")
        
        # Check for cached FAISS index
        if self._should_use_cached_analysis(video_id):
            logger.info(f"✅ Cached re-analysis enabled for media_id={video_id}")
            logger.info("Loaded FAISS index from cache")
            logger.info("Skipping full pipeline")
            try:
                return await self._analyze_video_cached(video_id, video_path, prompts, output_dir, previews_dir)
            except Exception as e:
                logger.warning(f"⚠️  Cached re-analysis failed: {e}")
                logger.warning("Falling back to full analysis pipeline...")
                # Continue with full analysis below
        
        # Full analysis pipeline
        return await self._analyze_video_full(video_id, video_path, prompts, output_dir, previews_dir)
    
    def _should_use_cached_analysis(self, video_id: str) -> bool:
        """Check if cached FAISS index exists for this video."""
        storage_config = self.config.get("storage", {})
        faiss_index_dir = storage_config.get("faiss_index_dir", "data/faiss_index")
        backend_root = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(faiss_index_dir):
            faiss_index_dir = os.path.join(backend_root, faiss_index_dir)
        
        indexer = FAISSIndexer(faiss_index_dir)
        return indexer.index_exists(video_id)
    
    async def _analyze_video_full(
        self,
        video_id: str,
        video_path: str,
        prompts: List[str],
        output_dir: str,
        previews_dir: str
    ) -> str:
        """Execute full analysis pipeline (frame extraction + CLIP encoding)."""
        # Prepare temp frame directory
        temp_frame_dir = os.path.join("temp_frames", video_id)
        os.makedirs(temp_frame_dir, exist_ok=True)
        
        try:
            # Step 1: Interpret prompts
            logger.info("\nStep 1: Interpreting prompts...")
            prompt_categories = await interpret_multiple_prompts(prompts)
            
            all_labels = []
            for category_info in prompt_categories:
                labels = category_info.get("labels", [])
                if labels:
                    all_labels.extend(labels)
                else:
                    prompt = category_info.get("prompt", "")
                    all_labels.append(prompt)
            
            all_labels = list(set(all_labels))
            logger.info(f"   Extracted {len(all_labels)} unique labels: {all_labels}")
            
            # Step 2: Extract frames
            logger.info("\nStep 2: Extracting frames...")
            # Support both new and legacy config structure
            frame_extraction_config = self.config.get('frame_extraction', {})
            sampling_rate = frame_extraction_config.get('sampling_rate', 5)
            frames_data = extract_frames(video_path, temp_frame_dir, sampling_rate=sampling_rate)
            frames = [cv2.imread(fd['frame_path']) for fd in frames_data]
            timestamps = [fd['timestamp_seconds'] for fd in frames_data]
            logger.info(f"   Extracted {len(frames)} frames")
            
            # Step 3: Encode text prompts
            logger.info("\nStep 3: Encoding text prompts...")
            text_features = self.encode_text_prompts(all_labels)
            logger.info(f"   Encoded {len(all_labels)} text prompts")
            
            # Step 4: Process frames and detect matches
            logger.info("\nStep 4: Processing frames...")
            # Support both new and legacy config structure
            if 'model' in self.config and 'batch_size' in self.config['model']:
                batch_size = self.config['model']['batch_size']
            else:
                batch_size = self.config.get('batch_size', 8)
            detection_results, all_embeddings, all_frame_indices, all_frame_timestamps = \
                self._process_frames_batch(frames, timestamps, text_features, all_labels, video_path, previews_dir)
            
            # Step 5: Build and save FAISS index
            logger.info(f"\nStep 5: Building FAISS index...")
            self._build_faiss_index(video_id, all_embeddings, all_frame_indices, all_frame_timestamps)
            
            # Step 6: Classify and save results
            logger.info(f"\nStep 6: Saving results...")
            results_file = self._save_results(video_id, detection_results, output_dir)
            
            logger.info(f"🎉 Analysis complete! Found {len(detection_results)} matches.")
            return results_file
            
        finally:
            # Clean up temp frame directory
            if os.path.exists(temp_frame_dir):
                shutil.rmtree(temp_frame_dir)
    
    def _process_frames_batch(
        self,
        frames: List[np.ndarray],
        timestamps: List[float],
        text_features: torch.Tensor,
        all_labels: List[str],
        video_path: str,
        previews_dir: str
    ) -> Tuple[List[DetectionResult], List[np.ndarray], List[int], List[float]]:
        """Process frames in batches and detect matches."""
        batch_size = self.config.get('batch_size', 8)
        detection_results = []
        all_embeddings = []
        all_frame_indices = []
        all_frame_timestamps = []
        frames_processed = 0
        
        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i:i + batch_size]
            batch_timestamps = timestamps[i:i + batch_size]
            logger.info(f"   Processing batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
            
            # Encode batch of frames
            image_features = self.encode_frames(batch_frames)
            
            # Collect embeddings for FAISS
            if isinstance(image_features, torch.Tensor):
                image_features_norm = image_features / image_features.norm(dim=-1, keepdim=True)
                batch_embeddings = image_features_norm.cpu().numpy()
            else:
                norms = np.linalg.norm(image_features, axis=1, keepdims=True)
                batch_embeddings = image_features / norms
            
            # Store embeddings for FAISS
            for j in range(len(batch_frames)):
                frame_idx = i + j
                all_embeddings.append(batch_embeddings[j])
                all_frame_indices.append(frame_idx)
                all_frame_timestamps.append(batch_timestamps[j])
            
            # Compare each frame with each text prompt
            for j, (frame, timestamp) in enumerate(zip(batch_frames, batch_timestamps)):
                frame_idx = i + j
                frames_processed += 1
                
                frame_features = image_features[j:j+1]
                similarities = []
                
                for k, label in enumerate(all_labels):
                    text_feature = text_features[k:k+1]
                    similarity = self.calculate_similarity(frame_features, text_feature)
                    similarities.append((label, similarity))
                
                # Log every ~30 frames
                if frames_processed % 30 == 0:
                    top_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
                    logger.debug(f"frame={frame_idx} ts={timestamp:.1f}s top3={top_similarities}")
                
                # Find matches above threshold
                matches = [(label, sim) for label, sim in similarities if sim >= self.similarity_threshold]
                
                if matches:
                    matches.sort(key=lambda x: x[1], reverse=True)
                    
                    timestamp_str = f"{int(timestamp//3600):02d}:{int((timestamp%3600)//60):02d}:{int(timestamp%60):02d}"
                    
                    # Generate preview path (support both new and legacy config)
                    preview_config = self.config.get("preview", {})
                    if preview_config:
                        preview_generation_enabled = preview_config.get("generation", {}).get("enabled", False)
                    else:
                        preview_generation_enabled = self.config.get("preview_generation", {}).get("enabled", False)
                    if preview_generation_enabled:
                        preview_path = generate_preview_clip(
                            video_path, 
                            previews_dir, 
                            timestamp_str, 
                            clip_length=3
                        )
                    else:
                        preview_path = f"virtual_preview_{timestamp_str.replace(':', '_')}"
                    
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
        
        return detection_results, all_embeddings, all_frame_indices, all_frame_timestamps
    
    def _build_faiss_index(
        self,
        video_id: str,
        all_embeddings: List[np.ndarray],
        all_frame_indices: List[int],
        all_frame_timestamps: List[float]
    ):
        """Build and save FAISS index for the video."""
        try:
            storage_config = self.config.get("storage", {})
            faiss_index_dir = storage_config.get("faiss_index_dir", "data/faiss_index")
            backend_root = os.path.dirname(os.path.abspath(__file__))
            if not os.path.isabs(faiss_index_dir):
                faiss_index_dir = os.path.join(backend_root, faiss_index_dir)
            
            logger.info(f"   FAISS index directory: {faiss_index_dir}")
            
            indexer = FAISSIndexer(faiss_index_dir)
            
            if len(all_embeddings) > 0:
                embeddings_array = np.array(all_embeddings)
                logger.info(f"   Collected {len(all_embeddings)} embeddings for FAISS indexing")
                
                success = indexer.build_and_save_index(
                    media_id=video_id,
                    embeddings=embeddings_array,
                    frame_indices=all_frame_indices,
                    timestamps=all_frame_timestamps
                )
                
                if success:
                    logger.info(f"✅ FAISS index saved successfully for {video_id}")
                else:
                    logger.warning(f"⚠️  Failed to save FAISS index for {video_id}")
            else:
                logger.warning("⚠️  No embeddings collected, skipping FAISS index creation")
                
        except Exception as e:
            logger.error(f"❌ Error building FAISS index: {e}", exc_info=True)
            # Don't fail the entire analysis if FAISS indexing fails
    
    def _save_results(
        self,
        video_id: str,
        detection_results: List[DetectionResult],
        output_dir: str
    ) -> str:
        """Classify detections and save results to JSON file."""
        # Convert DetectionResult objects to dictionaries
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
        
        # Classify alerts
        logger.info(f"   Classifying alerts...")
        classified_detections = classify_detections(detection_dicts)
        alert_summary = get_alert_summary(classified_detections)
        
        logger.info(f"📊 Alert Summary:")
        logger.info(f"   Total detections: {alert_summary['total_detections']}")
        logger.info(f"   Categories: {alert_summary['categories']}")
        logger.info(f"   Priorities: {alert_summary['priorities']}")
        
        # Save JSON results
        json_dir = os.path.join(output_dir, "json")
        os.makedirs(json_dir, exist_ok=True)
        results_file = os.path.join(json_dir, f"{video_id}.json")
        
        json_results = []
        for result in classified_detections:
            json_result = result.copy()
            if 'prompt_matches' in json_result and json_result['prompt_matches']:
                json_result['prompt_matches'] = [
                    (label, float(sim)) for label, sim in json_result['prompt_matches']
                ]
            json_results.append(json_result)
        
        final_results = {
            "detections": json_results,
            "alert_summary": alert_summary,
            "video_id": video_id,
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Saved {len(classified_detections)} detections to {results_file}")
        return results_file
    
    async def _analyze_video_cached(
        self,
        media_id: str,
        video_path: str,
        prompts: List[str],
        output_dir: str,
        previews_dir: str
    ) -> str:
        """Execute cached re-analysis using existing FAISS index."""
        logger.info(f"\n=== CACHED RE-ANALYSIS MODE ===")
        logger.info(f"Media ID: {media_id}")
        logger.info(f"Prompts: {prompts}")
        
        try:
            # Step 1: Interpret prompts
            logger.info("\nStep 1: Interpreting prompts...")
            prompt_categories = await interpret_multiple_prompts(prompts)
            
            all_labels = []
            for category_info in prompt_categories:
                labels = category_info.get("labels", [])
                if labels:
                    all_labels.extend(labels)
                else:
                    prompt = category_info.get("prompt", "")
                    all_labels.append(prompt)
            
            all_labels = list(set(all_labels))
            logger.info(f"   Extracted {len(all_labels)} unique labels: {all_labels}")
            
            # Step 2: Load FAISS index and metadata
            logger.info("\nStep 2: Loading FAISS index and metadata...")
            storage_config = self.config.get("storage", {})
            faiss_index_dir = storage_config.get("faiss_index_dir", "data/faiss_index")
            backend_root = os.path.dirname(os.path.abspath(__file__))
            if not os.path.isabs(faiss_index_dir):
                faiss_index_dir = os.path.join(backend_root, faiss_index_dir)
            
            indexer = FAISSIndexer(faiss_index_dir)
            metadata = indexer.load_metadata(media_id)
            if not metadata:
                raise Exception(f"Failed to load FAISS metadata for {media_id}")
            
            frame_indices = metadata.get("frame_indices", [])
            timestamps = metadata.get("timestamps", [])
            logger.info(f"   Loaded index with {metadata.get('num_vectors', 0)} vectors")
            
            # Step 3: Encode text prompts only
            logger.info("\nStep 3: Encoding text prompts...")
            text_features = self.encode_text_prompts(all_labels)
            logger.info(f"   Encoded {len(all_labels)} text prompts")
            
            # Convert text features to numpy for FAISS search
            if isinstance(text_features, torch.Tensor):
                text_features_norm = text_features / text_features.norm(dim=-1, keepdim=True)
                text_embeddings = text_features_norm.cpu().numpy().astype(np.float32)
            else:
                norms = np.linalg.norm(text_features, axis=1, keepdims=True)
                text_embeddings = text_features / norms
            
            # Step 4: Search FAISS index
            logger.info("\nStep 4: Searching FAISS index...")
            top_k = min(100, metadata.get("num_vectors", 100))
            search_results = indexer.search_index(media_id, text_embeddings, top_k=top_k)
            
            if search_results is None:
                raise Exception(f"FAISS search failed for {media_id}")
            
            distances, indices = search_results
            logger.info(f"   Search completed: {len(indices[0])} results per prompt")
            
            # Step 5: Process search results
            logger.info("\nStep 5: Processing search results...")
            detection_results = []
            
            for prompt_idx, label in enumerate(all_labels):
                prompt_distances = distances[prompt_idx]
                prompt_indices = indices[prompt_idx]
                
                for result_idx, (faiss_idx, distance) in enumerate(zip(prompt_indices, prompt_distances)):
                    similarity = float(distance)
                    
                    if similarity >= self.similarity_threshold:
                        frame_idx = frame_indices[faiss_idx] if faiss_idx < len(frame_indices) else faiss_idx
                        timestamp_seconds = timestamps[faiss_idx] if faiss_idx < len(timestamps) else 0.0
                        timestamp_str = f"{int(timestamp_seconds//3600):02d}:{int((timestamp_seconds%3600)//60):02d}:{int(timestamp_seconds%60):02d}"
                        preview_path = f"virtual_preview_{timestamp_str.replace(':', '_')}"
                        
                        result = DetectionResult(
                            timestamp=timestamp_str,
                            labels=[label],
                            confidence=similarity,
                            preview_clip=preview_path,
                            frame_index=frame_idx,
                            prompt_matches=[(label, similarity)]
                        )
                        
                        detection_results.append(result)
                        logger.info(f"✅ Match at {timestamp_str}: {label} (confidence: {similarity:.3f})")
            
            # Remove duplicates
            seen_frames = {}
            unique_detections = []
            for result in detection_results:
                key = (result.frame_index, result.timestamp)
                if key not in seen_frames:
                    seen_frames[key] = result
                    unique_detections.append(result)
                else:
                    existing = seen_frames[key]
                    existing.labels = list(set(existing.labels + result.labels))
                    existing.confidence = max(existing.confidence, result.confidence)
            
            detection_results = unique_detections
            logger.info(f"   Found {len(detection_results)} unique detections after deduplication")
            
            # Step 6: Save results
            logger.info(f"\nStep 6: Saving results...")
            results_file = self._save_results(media_id, detection_results, output_dir)
            
            logger.info(f"🎉 Cached analysis complete! Found {len(detection_results)} matches.")
            return results_file
            
        except Exception as e:
            logger.error(f"❌ Error in cached re-analysis: {e}", exc_info=True)
            raise

