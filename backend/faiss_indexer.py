"""
FAISS Vector Indexing Module

Provides functionality to build, save, and load FAISS indexes for video frame embeddings.
Each video/media_id gets its own FAISS index file and metadata JSON.
"""

import os
import json
import logging
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import faiss

logger = logging.getLogger("faiss_indexer")


class FAISSIndexer:
    """Manages FAISS indexes for video frame embeddings."""
    
    def __init__(self, index_dir: str):
        """
        Initialize FAISS indexer.
        
        Args:
            index_dir (str): Directory to store FAISS index files
        """
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        logger.info(f"FAISS indexer initialized with directory: {index_dir}")
    
    def _normalize_media_id(self, media_id: str) -> str:
        """Strip 'video_' prefix from media_id for clean file naming."""
        if media_id.startswith("video_"):
            return media_id[6:]  # Remove "video_" prefix (6 chars)
        return media_id
    
    def _get_index_path(self, media_id: str) -> str:
        """Get path to FAISS index file for a media_id."""
        clean_id = self._normalize_media_id(media_id)
        return os.path.join(self.index_dir, f"{clean_id}.index")
    
    def _get_metadata_path(self, media_id: str) -> str:
        """Get path to metadata JSON file for a media_id."""
        clean_id = self._normalize_media_id(media_id)
        return os.path.join(self.index_dir, f"{clean_id}.faiss-meta.json")
    
    def build_and_save_index(
        self,
        media_id: str,
        embeddings: np.ndarray,
        frame_indices: List[int],
        timestamps: List[float]
    ) -> bool:
        """
        Build and save a FAISS index for a video's frame embeddings.
        
        Args:
            media_id (str): Unique identifier for the video/media
            embeddings (np.ndarray): CLIP embeddings array of shape [num_frames, embedding_dim]
            frame_indices (List[int]): Frame indices corresponding to each embedding
            timestamps (List[float]): Timestamps in seconds for each frame
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            index_path = self._get_index_path(media_id)
            metadata_path = self._get_metadata_path(media_id)
            
            # Check if index already exists and is consistent
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        existing_meta = json.load(f)
                    existing_num_vectors = existing_meta.get("num_vectors", 0)
                    if existing_num_vectors == len(embeddings):
                        logger.info(
                            f"FAISS index for {media_id} already exists with {existing_num_vectors} vectors. "
                            "Skipping rebuild."
                        )
                        return True
                except Exception as e:
                    logger.warning(f"Could not read existing metadata for {media_id}: {e}. Rebuilding index.")
            
            # Validate inputs
            if len(embeddings) == 0:
                logger.error(f"Cannot build index for {media_id}: no embeddings provided")
                return False
            
            if len(embeddings) != len(frame_indices) or len(embeddings) != len(timestamps):
                logger.error(
                    f"Mismatch in lengths: embeddings={len(embeddings)}, "
                    f"frame_indices={len(frame_indices)}, timestamps={len(timestamps)}"
                )
                return False
            
            # Get embedding dimension
            embedding_dim = embeddings.shape[1] if len(embeddings.shape) > 1 else embeddings.shape[0]
            
            # Convert embeddings to float32 numpy array (FAISS requirement)
            if isinstance(embeddings, np.ndarray):
                embeddings_array = embeddings.astype(np.float32)
            else:
                # Handle torch tensors
                import torch
                if isinstance(embeddings, torch.Tensor):
                    embeddings_array = embeddings.cpu().numpy().astype(np.float32)
                else:
                    embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Ensure 2D array
            if len(embeddings_array.shape) == 1:
                embeddings_array = embeddings_array.reshape(1, -1)
            
            # Create FAISS index (using Inner Product for normalized CLIP embeddings)
            # IndexFlatIP works well with normalized CLIP embeddings
            index = faiss.IndexFlatIP(embedding_dim)
            
            # Normalize embeddings (CLIP embeddings should already be normalized, but ensure it)
            faiss.normalize_L2(embeddings_array)
            
            # Add embeddings to index
            index.add(embeddings_array)
            
            # Verify index
            if index.ntotal != len(embeddings):
                logger.error(f"Index size mismatch: expected {len(embeddings)}, got {index.ntotal}")
                return False
            
            # Save FAISS index
            faiss.write_index(index, index_path)
            logger.info(f"Saved FAISS index to {index_path} ({index.ntotal} vectors)")
            
            # Save metadata
            metadata = {
                "media_id": media_id,
                "embedding_dim": int(embedding_dim),
                "num_vectors": int(index.ntotal),
                "frame_indices": frame_indices,
                "timestamps": timestamps
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved metadata to {metadata_path}")
            logger.info(f"✅ Successfully built and saved FAISS index for {media_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index for {media_id}: {e}", exc_info=True)
            return False
    
    def load_index(self, media_id: str) -> Optional[faiss.Index]:
        """
        Load a FAISS index from disk.
        
        Args:
            media_id (str): Unique identifier for the video/media
            
        Returns:
            Optional[faiss.Index]: FAISS index if found, None otherwise
        """
        try:
            index_path = self._get_index_path(media_id)
            
            if not os.path.exists(index_path):
                logger.warning(f"FAISS index not found for {media_id} at {index_path}")
                return None
            
            index = faiss.read_index(index_path)
            logger.info(f"Loaded FAISS index for {media_id} ({index.ntotal} vectors)")
            return index
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index for {media_id}: {e}", exc_info=True)
            return None
    
    def load_metadata(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Load metadata JSON for a FAISS index.
        
        Args:
            media_id (str): Unique identifier for the video/media
            
        Returns:
            Optional[Dict]: Metadata dictionary if found, None otherwise
        """
        try:
            metadata_path = self._get_metadata_path(media_id)
            
            if not os.path.exists(metadata_path):
                logger.warning(f"Metadata not found for {media_id} at {metadata_path}")
                return None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            logger.debug(f"Loaded metadata for {media_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata for {media_id}: {e}", exc_info=True)
            return None
    
    def search_index(
        self,
        media_id: str,
        query_vectors: np.ndarray,
        top_k: int = 10
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Search a FAISS index with query vectors.
        
        Args:
            media_id (str): Unique identifier for the video/media
            query_vectors (np.ndarray): Query embeddings of shape [num_queries, embedding_dim]
            top_k (int): Number of nearest neighbors to return
            
        Returns:
            Optional[Tuple]: (distances, indices) arrays if successful, None otherwise
            - distances: shape [num_queries, top_k] - similarity scores
            - indices: shape [num_queries, top_k] - FAISS row indices
        """
        try:
            index = self.load_index(media_id)
            if index is None:
                return None
            
            # Convert query vectors to float32
            if isinstance(query_vectors, np.ndarray):
                query_array = query_vectors.astype(np.float32)
            else:
                import torch
                if isinstance(query_vectors, torch.Tensor):
                    query_array = query_vectors.cpu().numpy().astype(np.float32)
                else:
                    query_array = np.array(query_vectors, dtype=np.float32)
            
            # Ensure 2D array
            if len(query_array.shape) == 1:
                query_array = query_array.reshape(1, -1)
            
            # Normalize query vectors
            faiss.normalize_L2(query_array)
            
            # Search
            k = min(top_k, index.ntotal)  # Don't request more than available
            distances, indices = index.search(query_array, k)
            
            logger.debug(f"Searched index for {media_id}: found {len(indices[0])} results")
            return distances, indices
            
        except Exception as e:
            logger.error(f"Failed to search FAISS index for {media_id}: {e}", exc_info=True)
            return None
    
    def index_exists(self, media_id: str) -> bool:
        """
        Check if a FAISS index exists for a media_id.
        Supports both new format (clean ID) and old format (with video_ prefix) for backward compatibility.
        
        Args:
            media_id (str): Unique identifier for the video/media
            
        Returns:
            bool: True if both index and metadata files exist
        """
        # Check new format (normalized, without prefix)
        index_path = self._get_index_path(media_id)
        metadata_path = self._get_metadata_path(media_id)
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            return True
        
        # Backward compatibility: check old format (with prefix) if media_id doesn't already have it
        if not media_id.startswith("video_"):
            old_index_path = os.path.join(self.index_dir, f"video_{media_id}.index")
            old_metadata_path = os.path.join(self.index_dir, f"video_{media_id}.faiss-meta.json")
            if os.path.exists(old_index_path) and os.path.exists(old_metadata_path):
                return True
        
        return False

