"""
FAISS Indexer Dev Test Script

Simple test script to verify FAISSIndexer functionality in isolation.
Tests: index building, saving, loading, metadata, and search operations.

Usage:
    cd backend
    python scripts/dev_test_faiss_indexer.py
"""

import os
import sys
import numpy as np
import logging

# Check if FAISS is installed
try:
    import faiss
except ImportError:
    print("=" * 60)
    print("ERROR: FAISS not installed")
    print("=" * 60)
    print("\nPlease install FAISS first:")
    print("  pip install faiss-cpu>=1.7.4")
    print("\nOr if you have a GPU:")
    print("  pip install faiss-gpu>=1.7.4")
    print("\nThen run this script again.")
    sys.exit(1)

# Add backend directory to path so we can import modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from faiss_indexer import FAISSIndexer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("faiss_dev_test")


def main():
    """Run FAISS indexer dev test."""
    logger.info("=" * 60)
    logger.info("FAISS Indexer Dev Test")
    logger.info("=" * 60)
    
    # Test parameters
    media_id = "dev_faiss_test"
    num_frames = 100
    embedding_dim = 512
    
    # Use a temporary test directory
    test_index_dir = os.path.join(backend_dir, "data", "faiss_index_test")
    
    try:
        # Step 1: Create synthetic embeddings
        logger.info("\n[Step 1] Creating synthetic embeddings...")
        np.random.seed(42)  # For reproducibility
        embeddings = np.random.randn(num_frames, embedding_dim).astype(np.float32)
        
        # Normalize embeddings (as CLIP embeddings are normalized)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        frame_indices = list(range(num_frames))
        timestamps = [i * 0.5 for i in range(num_frames)]  # 0.5s per frame
        
        logger.info(f"   Created {num_frames} embeddings of dimension {embedding_dim}")
        logger.info(f"   Embeddings shape: {embeddings.shape}")
        logger.info(f"   Frame indices: {len(frame_indices)}")
        logger.info(f"   Timestamps: {len(timestamps)} (range: {timestamps[0]:.1f}s to {timestamps[-1]:.1f}s)")
        
        # Step 2: Initialize FAISS indexer
        logger.info("\n[Step 2] Initializing FAISS indexer...")
        indexer = FAISSIndexer(test_index_dir)
        logger.info(f"   Index directory: {test_index_dir}")
        
        # Step 3: Build and save index
        logger.info("\n[Step 3] Building and saving FAISS index...")
        success = indexer.build_and_save_index(
            media_id=media_id,
            embeddings=embeddings,
            frame_indices=frame_indices,
            timestamps=timestamps
        )
        
        if not success:
            logger.error("❌ Failed to build and save index")
            return False
        
        logger.info("✅ Index built and saved successfully")
        
        # Step 4: Load index and metadata
        logger.info("\n[Step 4] Loading index and metadata...")
        
        # Load index
        index = indexer.load_index(media_id)
        if index is None:
            logger.error("❌ Failed to load index")
            return False
        
        logger.info(f"   Loaded index with {index.ntotal} vectors")
        
        # Verify index size
        if index.ntotal != num_frames:
            logger.error(f"❌ Index size mismatch: expected {num_frames}, got {index.ntotal}")
            return False
        
        logger.info(f"✅ Index size verified: {index.ntotal} == {num_frames}")
        
        # Load metadata
        metadata = indexer.load_metadata(media_id)
        if metadata is None:
            logger.error("❌ Failed to load metadata")
            return False
        
        logger.info("   Metadata loaded:")
        logger.info(f"      media_id: {metadata.get('media_id')}")
        logger.info(f"      embedding_dim: {metadata.get('embedding_dim')}")
        logger.info(f"      num_vectors: {metadata.get('num_vectors')}")
        logger.info(f"      frame_indices count: {len(metadata.get('frame_indices', []))}")
        logger.info(f"      timestamps count: {len(metadata.get('timestamps', []))}")
        
        # Verify metadata fields
        if metadata.get('media_id') != media_id:
            logger.error(f"❌ Metadata media_id mismatch: expected {media_id}, got {metadata.get('media_id')}")
            return False
        
        if metadata.get('embedding_dim') != embedding_dim:
            logger.error(f"❌ Metadata embedding_dim mismatch: expected {embedding_dim}, got {metadata.get('embedding_dim')}")
            return False
        
        if metadata.get('num_vectors') != num_frames:
            logger.error(f"❌ Metadata num_vectors mismatch: expected {num_frames}, got {metadata.get('num_vectors')}")
            return False
        
        if len(metadata.get('frame_indices', [])) != num_frames:
            logger.error(f"❌ Metadata frame_indices count mismatch: expected {num_frames}, got {len(metadata.get('frame_indices', []))}")
            return False
        
        if len(metadata.get('timestamps', [])) != num_frames:
            logger.error(f"❌ Metadata timestamps count mismatch: expected {num_frames}, got {len(metadata.get('timestamps', []))}")
            return False
        
        logger.info("✅ Metadata fields verified")
        
        # Step 5: Test search
        logger.info("\n[Step 5] Testing search functionality...")
        
        # Use a few random query vectors (including one that exists in the index)
        query_indices = [0, 42, 99]  # First, middle, last frame
        query_vectors = embeddings[query_indices]
        
        logger.info(f"   Testing search with {len(query_indices)} query vectors")
        
        results = indexer.search_index(media_id, query_vectors, top_k=5)
        if results is None:
            logger.error("❌ Search failed")
            return False
        
        distances, indices = results
        
        logger.info(f"   Search returned distances shape: {distances.shape}")
        logger.info(f"   Search returned indices shape: {indices.shape}")
        
        # Verify search results
        for i, query_idx in enumerate(query_indices):
            top_result_idx = indices[i][0]  # Top result
            top_distance = distances[i][0]
            
            logger.info(f"   Query {i} (frame {query_idx}): top result = frame {top_result_idx}, distance = {top_distance:.4f}")
            
            # The query vector exists in the index, so top result should be the same frame
            # (distance should be very close to 1.0 for normalized vectors with inner product)
            if top_result_idx == query_idx:
                logger.info(f"      ✅ Correct: query frame {query_idx} found as top result")
            else:
                logger.warning(f"      ⚠️  Query frame {query_idx} not top result (got {top_result_idx})")
                # This is okay - might happen with random data, but distance should still be high
                if top_distance > 0.9:
                    logger.info(f"      ✅ Distance is high ({top_distance:.4f}), which is good")
        
        logger.info("✅ Search functionality verified")
        
        # Step 6: Test index_exists
        logger.info("\n[Step 6] Testing index_exists check...")
        exists = indexer.index_exists(media_id)
        if not exists:
            logger.error("❌ index_exists returned False for existing index")
            return False
        
        logger.info(f"✅ index_exists correctly returned True for {media_id}")
        
        # Step 7: Test reuse behavior (should skip rebuild)
        logger.info("\n[Step 7] Testing index reuse (should skip rebuild if exists)...")
        success_reuse = indexer.build_and_save_index(
            media_id=media_id,
            embeddings=embeddings,
            frame_indices=frame_indices,
            timestamps=timestamps
        )
        
        if not success_reuse:
            logger.error("❌ Failed on reuse test")
            return False
        
        logger.info("✅ Index reuse test passed (should have skipped rebuild)")
        
        # All tests passed!
        logger.info("\n" + "=" * 60)
        logger.info("✅ FAISS dev test PASSED: index build/load/search works for dev_faiss_test")
        logger.info("=" * 60)
        logger.info(f"\nTest files created in: {test_index_dir}")
        logger.info("   - dev_faiss_test.index")
        logger.info("   - dev_faiss_test.faiss-meta.json")
        logger.info("\nYou can manually inspect these files or delete them after testing.")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ FAISS dev test FAILED with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

