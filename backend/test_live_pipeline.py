"""
Test script for Live Stream Processing Pipeline.

Tests the pipeline with a video file simulation.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from live_pipeline import LivePipeline, create_pipeline_from_config
from live_detector import Alert
from config_loader import load_clip_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def alert_handler(alert: Alert):
    """Handle alert callback."""
    logger.info(f"🚨 ALERT: {alert.labels} @ {alert.timestamp_seconds:.2f}s (confidence: {alert.confidence:.3f})")


async def test_with_video_file():
    """Test pipeline with a video file."""
    logger.info("=" * 60)
    logger.info("Testing Live Pipeline with Video File")
    logger.info("=" * 60)
    
    # Find a test video file
    upload_dir = Path("content/uploads")
    video_files = list(upload_dir.glob("*.mp4"))
    
    if not video_files:
        logger.error(f"No video files found in {upload_dir}")
        logger.info("Please add a test video file to content/uploads/")
        return
    
    test_video = str(video_files[0])
    logger.info(f"Using test video: {test_video}")
    
    # Load config
    config = load_clip_config()
    
    # Create pipeline
    prompts = ["person", "people", "car", "vehicle", "fire"]
    logger.info(f"Detection prompts: {prompts}")
    
    pipeline = LivePipeline(
        source=test_video,
        prompts=prompts,
        config=config,
        target_fps=1.0,  # 1 frame per second
        similarity_threshold=0.21
    )
    
    # Add alert callback
    pipeline.add_alert_callback(alert_handler)
    
    # Start pipeline
    logger.info("Starting pipeline...")
    if not await pipeline.start():
        logger.error("Failed to start pipeline")
        return
    
    try:
        # Run for 30 seconds or until stopped
        logger.info("Pipeline running... (press Ctrl+C to stop)")
        logger.info("Waiting for alerts...")
        
        alert_count = 0
        max_duration = 30  # seconds
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_duration:
                logger.info(f"Reached max duration ({max_duration}s), stopping...")
                break
            
            # Get alert (non-blocking)
            alert = pipeline.get_alert(timeout=1.0)
            if alert:
                alert_count += 1
                logger.info(f"Received alert #{alert_count}: {alert.labels} @ {alert.timestamp_seconds:.2f}s")
            
            # Print stats periodically
            if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                stats = pipeline.get_stats()
                logger.info(f"Stats: {stats}")
            
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop pipeline
        logger.info("Stopping pipeline...")
        pipeline.stop()
        
        # Print final stats
        stats = pipeline.get_stats()
        logger.info("=" * 60)
        logger.info("Final Statistics:")
        logger.info(f"  Frames captured: {stats['source']['frames_captured']}")
        logger.info(f"  Frames processed: {stats['detector']['frames_processed']}")
        logger.info(f"  Alerts emitted: {stats['detector']['alerts_emitted']}")
        logger.info("=" * 60)


async def test_with_config():
    """Test pipeline using config file."""
    logger.info("=" * 60)
    logger.info("Testing Live Pipeline with Config File")
    logger.info("=" * 60)
    
    # Load config
    config = load_clip_config()
    
    # Set test video in config (temporary)
    upload_dir = Path("content/uploads")
    video_files = list(upload_dir.glob("*.mp4"))
    
    if not video_files:
        logger.error(f"No video files found in {upload_dir}")
        return
    
    test_video = str(video_files[0])
    config['live_stream']['source'] = test_video
    config['live_stream']['prompts'] = ["person", "car", "fire"]
    config['live_stream']['target_fps'] = 1.0
    
    # Create pipeline from config
    pipeline = await create_pipeline_from_config(config)
    
    if not pipeline:
        logger.error("Failed to create pipeline from config")
        return
    
    # Add alert callback
    pipeline.add_alert_callback(alert_handler)
    
    # Start pipeline
    logger.info("Starting pipeline...")
    if not await pipeline.start():
        logger.error("Failed to start pipeline")
        return
    
    try:
        logger.info("Pipeline running... (press Ctrl+C to stop)")
        
        alert_count = 0
        max_duration = 20  # seconds
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_duration:
                break
            
            alert = pipeline.get_alert(timeout=1.0)
            if alert:
                alert_count += 1
            
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        pipeline.stop()
        stats = pipeline.get_stats()
        logger.info(f"Final stats: {stats}")


async def main():
    """Main test function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        await test_with_config()
    else:
        await test_with_video_file()


if __name__ == "__main__":
    asyncio.run(main())

