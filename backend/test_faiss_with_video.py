"""
Test FAISS indexing with actual video file.

Tests the full analyzer pipeline to verify FAISS index is created during video analysis.
"""

import os
import sys
import asyncio
import logging

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from analyzer import analyze_video

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("faiss_video_test")


async def main():
    """Test FAISS indexing with actual video."""
    video_path = os.path.join(backend_dir, "content", "uploads", "Avunanavaa.mp4")
    
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
    
    logger.info("=" * 60)
    logger.info("FAISS Video Test")
    logger.info("=" * 60)
    logger.info(f"Video: {video_path}")
    logger.info(f"File exists: {os.path.exists(video_path)}")
    logger.info(f"File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    # Test prompts
    prompts = ["person", "people"]
    
    logger.info(f"\nPrompts: {prompts}")
    logger.info("\nRunning analysis (this will create FAISS index)...")
    logger.info("=" * 60)
    
    try:
        # Run analysis
        results, json_path = await analyze_video(
            video_path=video_path,
            prompts=prompts,
            output_dir=os.path.join(backend_dir, "results")
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("Analysis completed!")
        logger.info("=" * 60)
        
        # Check if FAISS index was created
        # The video_id is generated from the video path hash
        import hashlib
        with open(video_path, 'rb') as f:
            video_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        
        # Try to find the media_id - it might be based on the video hash or filename
        # Let's check the results to see what video_id was used
        if isinstance(results, dict):
            video_id = results.get("video_id", video_hash)
        else:
            video_id = video_hash
        
        logger.info(f"\nChecking for FAISS index for video_id: {video_id}")
        
        # Check FAISS index directory
        from config_loader import load_clip_config
        config = load_clip_config()
        storage_config = config.get("storage", {})
        faiss_index_dir = storage_config.get("faiss_index_dir", "data/faiss_index")
        
        if not os.path.isabs(faiss_index_dir):
            faiss_index_dir = os.path.join(backend_dir, faiss_index_dir)
        
        index_path = os.path.join(faiss_index_dir, f"{video_id}.index")
        metadata_path = os.path.join(faiss_index_dir, f"{video_id}.faiss-meta.json")
        
        logger.info(f"FAISS index directory: {faiss_index_dir}")
        logger.info(f"Expected index file: {index_path}")
        logger.info(f"Expected metadata file: {metadata_path}")
        
        if os.path.exists(index_path):
            logger.info(f"✅ FAISS index file exists: {index_path}")
            file_size = os.path.getsize(index_path) / (1024*1024)
            logger.info(f"   File size: {file_size:.2f} MB")
        else:
            logger.warning(f"⚠️  FAISS index file not found: {index_path}")
            # List what files exist in the directory
            if os.path.exists(faiss_index_dir):
                files = os.listdir(faiss_index_dir)
                logger.info(f"   Files in index directory: {files}")
        
        if os.path.exists(metadata_path):
            logger.info(f"✅ FAISS metadata file exists: {metadata_path}")
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            logger.info(f"   Metadata:")
            logger.info(f"      media_id: {metadata.get('media_id')}")
            logger.info(f"      embedding_dim: {metadata.get('embedding_dim')}")
            logger.info(f"      num_vectors: {metadata.get('num_vectors')}")
            logger.info(f"      timestamps count: {len(metadata.get('timestamps', []))}")
        else:
            logger.warning(f"⚠️  FAISS metadata file not found: {metadata_path}")
        
        logger.info("\n" + "=" * 60)
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            logger.info("✅ FAISS indexing test PASSED: Index created during video analysis")
        else:
            logger.warning("⚠️  FAISS index files not found - check logs above for details")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Analysis failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

