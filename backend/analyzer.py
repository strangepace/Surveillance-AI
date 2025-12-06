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
from faiss_indexer import FAISSIndexer

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
    
    async def analyze_video(self, video_path: str, prompts: List[str], output_dir: str, media_id: Optional[str] = None) -> str:
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
        storage_config = self.config.get("storage", {})
        faiss_index_dir = storage_config.get("faiss_index_dir", "data/faiss_index")
        backend_root = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(faiss_index_dir):
            faiss_index_dir = os.path.join(backend_root, faiss_index_dir)
        
        indexer = FAISSIndexer(faiss_index_dir)
        
        # Check if cached index exists
        if indexer.index_exists(video_id):
            logger.info(f"✅ Cached re-analysis enabled for media_id={video_id}")
            logger.info("Loaded FAISS index from cache")
            logger.info("Skipping full pipeline")
            try:
                return await self._analyze_video_cached(video_id, video_path, prompts, output_dir, previews_dir, indexer)
            except Exception as e:
                logger.warning(f"⚠️  Cached re-analysis failed: {e}")
                logger.warning("Falling back to full analysis pipeline...")
                # Continue with full analysis below

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
            
            # Collect all embeddings for FAISS indexing
            all_embeddings = []
            all_frame_indices = []
            all_frame_timestamps = []
            
            for i in range(0, len(frames), batch_size):
                batch_frames = frames[i:i + batch_size]
                batch_timestamps = timestamps[i:i + batch_size]
                logger.info(f"   Processing batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
                # Encode batch of frames
                image_features = self.encode_frames(batch_frames)
                
                # Collect embeddings for FAISS (normalize and convert to numpy)
                import torch
                if isinstance(image_features, torch.Tensor):
                    # Normalize embeddings (CLIP embeddings should be normalized)
                    image_features_norm = image_features / image_features.norm(dim=-1, keepdim=True)
                    # Convert to CPU numpy for FAISS
                    batch_embeddings = image_features_norm.cpu().numpy()
                else:
                    # Already numpy, normalize
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
                        
                        # Generate preview clip (LEGACY SERVER PREVIEW GENERATION - kept for fallback)
                        timestamp_str = f"{int(timestamp//3600):02d}:{int((timestamp%3600)//60):02d}:{int(timestamp%60):02d}"
                        
                        # Check if legacy preview generation is enabled
                        preview_generation_enabled = self.config.get("preview_generation", {}).get("enabled", False)
                        if preview_generation_enabled:
                            preview_path = generate_preview_clip(
                                video_path, 
                                previews_dir, 
                                timestamp_str, 
                                clip_length=3
                            )
                        else:
                            # Virtual preview mode - just return a placeholder path
                            preview_path = f"virtual_preview_{timestamp_str.replace(':', '_')}"
                        
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
            
            # Step 4.5: Build and save FAISS index
            logger.info(f"\nStep 4.5: Building FAISS index...")
            try:
                # Get FAISS index directory from config
                storage_config = self.config.get("storage", {})
                faiss_index_dir = storage_config.get("faiss_index_dir", "data/faiss_index")
                
                # Resolve path relative to backend root (where analyzer.py is located)
                backend_root = os.path.dirname(os.path.abspath(__file__))
                if not os.path.isabs(faiss_index_dir):
                    faiss_index_dir = os.path.join(backend_root, faiss_index_dir)
                
                logger.info(f"   FAISS index directory: {faiss_index_dir}")
                
                # Initialize FAISS indexer
                indexer = FAISSIndexer(faiss_index_dir)
                
                # Convert embeddings list to numpy array
                if len(all_embeddings) > 0:
                    embeddings_array = np.array(all_embeddings)
                    logger.info(f"   Collected {len(all_embeddings)} embeddings for FAISS indexing")
                    
                    # Build and save index
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
            # Use video_id directly (it may already have 'video_' prefix)
            results_file = os.path.join(json_dir, f"{video_id}.json")
            
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
    
    async def _analyze_video_cached(
        self, 
        media_id: str, 
        video_path: str, 
        prompts: List[str], 
        output_dir: str, 
        previews_dir: str,
        indexer: FAISSIndexer
    ) -> str:
        """
        Cached re-analysis using existing FAISS index.
        Skips frame extraction and CLIP encoding of frames.
        
        Args:
            media_id (str): Media ID for the cached index
            video_path (str): Path to video file (for preview generation)
            prompts (List[str]): List of natural language prompts
            output_dir (str): Directory to store results
            previews_dir (str): Directory for preview clips
            indexer (FAISSIndexer): Initialized FAISS indexer
            
        Returns:
            str: Path to results JSON file
        """
        logger.info(f"\n=== CACHED RE-ANALYSIS MODE ===")
        logger.info(f"Media ID: {media_id}")
        logger.info(f"Prompts: {prompts}")
        
        try:
            # Step 1: Interpret prompts (same as full analysis)
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
            metadata = indexer.load_metadata(media_id)
            if not metadata:
                raise Exception(f"Failed to load FAISS metadata for {media_id}")
            
            frame_indices = metadata.get("frame_indices", [])
            timestamps = metadata.get("timestamps", [])
            logger.info(f"   Loaded index with {metadata.get('num_vectors', 0)} vectors")
            logger.info(f"   Frame indices: {len(frame_indices)}")
            logger.info(f"   Timestamps: {len(timestamps)}")
            
            # Step 3: Encode text prompts only (no frame encoding)
            logger.info("\nStep 3: Encoding text prompts...")
            text_features = self.encode_text_prompts(all_labels)
            logger.info(f"   Encoded {len(all_labels)} text prompts")
            
            # Convert text features to numpy for FAISS search
            import torch
            if isinstance(text_features, torch.Tensor):
                text_features_norm = text_features / text_features.norm(dim=-1, keepdim=True)
                text_embeddings = text_features_norm.cpu().numpy().astype(np.float32)
            else:
                norms = np.linalg.norm(text_features, axis=1, keepdims=True)
                text_embeddings = text_features / norms
            
            # Step 4: Search FAISS index
            logger.info("\nStep 4: Searching FAISS index...")
            top_k = min(100, metadata.get("num_vectors", 100))  # Search top 100 matches per prompt
            search_results = indexer.search_index(media_id, text_embeddings, top_k=top_k)
            
            if search_results is None:
                raise Exception(f"FAISS search failed for {media_id}")
            
            distances, indices = search_results
            logger.info(f"   Search completed: {len(indices[0])} results per prompt")
            
            # Step 5: Process search results and create detections
            logger.info("\nStep 5: Processing search results...")
            detection_results = []
            
            # Process each prompt's search results
            for prompt_idx, label in enumerate(all_labels):
                prompt_distances = distances[prompt_idx]
                prompt_indices = indices[prompt_idx]
                
                # Filter by similarity threshold
                for result_idx, (faiss_idx, distance) in enumerate(zip(prompt_indices, prompt_distances)):
                    # Convert FAISS distance (inner product) to similarity
                    # For normalized vectors, inner product = cosine similarity
                    similarity = float(distance)
                    
                    if similarity >= self.similarity_threshold:
                        # Map FAISS index to frame index and timestamp
                        frame_idx = frame_indices[faiss_idx] if faiss_idx < len(frame_indices) else faiss_idx
                        timestamp_seconds = timestamps[faiss_idx] if faiss_idx < len(timestamps) else 0.0
                        
                        # Format timestamp string
                        timestamp_str = f"{int(timestamp_seconds//3600):02d}:{int((timestamp_seconds%3600)//60):02d}:{int(timestamp_seconds%60):02d}"
                        
                        # Generate preview path (virtual preview mode)
                        preview_path = f"virtual_preview_{timestamp_str.replace(':', '_')}"
                        
                        # Create detection result
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
            
            # Remove duplicates (same frame matched by multiple prompts)
            seen_frames = {}
            unique_detections = []
            for result in detection_results:
                key = (result.frame_index, result.timestamp)
                if key not in seen_frames:
                    seen_frames[key] = result
                    unique_detections.append(result)
                else:
                    # Merge labels if same frame
                    existing = seen_frames[key]
                    existing.labels = list(set(existing.labels + result.labels))
                    existing.confidence = max(existing.confidence, result.confidence)
            
            detection_results = unique_detections
            logger.info(f"   Found {len(detection_results)} unique detections after deduplication")
            
            # Step 6: Classify and save results (same as full analysis)
            logger.info(f"\nStep 6: Classifying alerts...")
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
            
            # Save JSON results
            json_dir = os.path.join(output_dir, "json")
            os.makedirs(json_dir, exist_ok=True)
            # Use media_id directly (it may already have 'video_' prefix)
            results_file = os.path.join(json_dir, f"{media_id}.json")
            
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
                "video_id": media_id,
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "cached": True
            }
            
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2)
            
            logger.info(f"Saved {len(classified_detections)} detections to {results_file}")
            logger.info(f"🎉 Cached analysis complete! Found {len(classified_detections)} matches.")
            
            return results_file
            
        except Exception as e:
            logger.error(f"❌ Error in cached re-analysis: {e}", exc_info=True)
            raise
    
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
                # Generate preview clip (LEGACY SERVER PREVIEW GENERATION - kept for fallback)
                preview_generation_enabled = self.config.get("preview_generation", {}).get("enabled", False)
                if preview_generation_enabled:
                    preview_path = generate_preview_clip(
                        video_path, 
                        previews_dir, 
                        timestamp, 
                        clip_length=3
                    )
                else:
                    # Virtual preview mode - just return a placeholder path
                    preview_path = f"virtual_preview_{timestamp.replace(':', '_')}"
                
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
async def analyze_video(video_path: str, prompts: List[str], output_dir: str = "results", media_id: Optional[str] = None) -> tuple:
        """
        Main analysis function with comprehensive error handling.
        Supports cached re-analysis via media_id parameter.
        
        Args:
            video_path (str): Path to video file
            prompts (List[str]): List of prompts to search for
            output_dir (str): Directory to save results
            media_id (Optional[str]): Media ID for cached re-analysis
            
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
            
            # Run analysis (with optional media_id for cached mode)
            try:
                results_file = await analyzer.analyze_video(video_path, prompts, output_dir, media_id=media_id)
            except Exception as e:
                error_handler.log_error(e, ErrorType.FRAME_EXTRACTION, {
                    "video_path": video_path,
                    "prompts": prompts,
                    "output_dir": output_dir,
                    "media_id": media_id
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
