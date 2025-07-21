# backend_v3/test_frame_extractor.py
"""
Test script for frame_extractor.py module.
Tests frame extraction, timestamp naming, output directory creation, and metadata structure.
"""
import os
import tempfile
import shutil
from .frame_extractor import extract_frames, format_timestamp, get_video_info


def test_format_timestamp():
    """Test timestamp formatting function."""
    print("🧪 Testing timestamp formatting...")
    
    test_cases = [
        (0, "00:00:00"),
        (61, "00:01:01"),
        (3661, "01:01:01"),
        (7322, "02:02:02")
    ]
    
    for seconds, expected in test_cases:
        result = format_timestamp(seconds)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"  ✅ {seconds}s -> {result}")
    
    print("✅ Timestamp formatting tests passed")


def test_video_info():
    """Test video info extraction."""
    print("🧪 Testing video info extraction...")
    
    # Use a test video if available, otherwise skip
    test_video = "content/uploads/naani.mp4"
    if os.path.exists(test_video):
        info = get_video_info(test_video)
        print(f"  📹 Video info: {info}")
        assert "fps" in info, "Video info should contain fps"
        assert "total_frames" in info, "Video info should contain total_frames"
        assert "duration" in info, "Video info should contain duration"
        print("✅ Video info extraction test passed")
    else:
        print("  ⚠️  Test video not found, skipping video info test")


def test_frame_extraction():
    """Test frame extraction functionality."""
    print("🧪 Testing frame extraction...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"  📁 Using temp directory: {temp_dir}")
        
        # Test with a real video if available
        test_video = "content/uploads/naani.mp4"
        if os.path.exists(test_video):
            # Test basic extraction
            print("  🔍 Testing basic frame extraction...")
            metadata = extract_frames(
                video_path=test_video,
                output_dir=temp_dir,
                sampling_rate=30,  # Extract every 30th frame
                resize=False
            )
            
            # Verify results
            assert len(metadata) > 0, "Should extract at least one frame"
            print(f"  ✅ Extracted {len(metadata)} frames")
            
            # Check metadata structure
            for frame_data in metadata:
                assert "frame_path" in frame_data, "Metadata should contain frame_path"
                assert "timestamp" in frame_data, "Metadata should contain timestamp"
                assert "timestamp_seconds" in frame_data, "Metadata should contain timestamp_seconds"
                assert "frame_number" in frame_data, "Metadata should contain frame_number"
                
                # Check if file exists
                assert os.path.exists(frame_data["frame_path"]), f"Frame file should exist: {frame_data['frame_path']}"
            
            print("  ✅ Metadata structure is correct")
            print("  ✅ Frame files were created")
            
            # Test with resize
            print("  🔍 Testing frame extraction with resize...")
            metadata_resized = extract_frames(
                video_path=test_video,
                output_dir=os.path.join(temp_dir, "resized"),
                sampling_rate=60,  # Extract every 60th frame
                resize=True
            )
            
            assert len(metadata_resized) > 0, "Should extract at least one resized frame"
            print(f"  ✅ Extracted {len(metadata_resized)} resized frames")
            
            # Test with PIL Image objects
            print("  🔍 Testing frame extraction with PIL images...")
            metadata_with_images = extract_frames(
                video_path=test_video,
                output_dir=os.path.join(temp_dir, "with_images"),
                sampling_rate=90,  # Extract every 90th frame
                return_images=True
            )
            
            assert len(metadata_with_images) > 0, "Should extract at least one frame with images"
            for frame_data in metadata_with_images:
                assert "image" in frame_data, "Metadata should contain PIL Image object"
            
            print(f"  ✅ Extracted {len(metadata_with_images)} frames with PIL images")
            
        else:
            print("  ⚠️  Test video not found, creating dummy test...")
            # Create a dummy test video for testing
            create_dummy_video(temp_dir)
            
            dummy_video = os.path.join(temp_dir, "dummy.mp4")
            metadata = extract_frames(
                video_path=dummy_video,
                output_dir=os.path.join(temp_dir, "frames"),
                sampling_rate=1
            )
            
            assert len(metadata) > 0, "Should extract frames from dummy video"
            print(f"  ✅ Extracted {len(metadata)} frames from dummy video")
    
    print("✅ Frame extraction tests passed")


def create_dummy_video(output_dir):
    """Create a dummy video file for testing."""
    try:
        import cv2
        import numpy as np
        
        # Create a simple video with colored frames
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(os.path.join(output_dir, "dummy.mp4"), fourcc, 10.0, (320, 240))
        
        for i in range(30):  # 3 seconds at 10 fps
            # Create a colored frame
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            frame[:, :, 0] = (i * 8) % 256  # Blue channel
            frame[:, :, 1] = (i * 16) % 256  # Green channel
            frame[:, :, 2] = (i * 32) % 256  # Red channel
            
            out.write(frame)
        
        out.release()
        print("  📹 Created dummy test video")
        
    except ImportError:
        print("  ⚠️  OpenCV not available, skipping dummy video creation")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("🧪 Testing error handling...")
    
    # Test non-existent video file
    try:
        extract_frames("non_existent_video.mp4", "temp_dir")
        assert False, "Should raise FileNotFoundError"
    except FileNotFoundError:
        print("  ✅ Correctly handled non-existent video file")
    
    # Test invalid output directory (should create it)
    try:
        # This should work and create the directory
        test_video = "content/uploads/naani.mp4"
        if os.path.exists(test_video):
            extract_frames(test_video, "temp_test_dir", sampling_rate=1000)  # Very high sampling rate
            print("  ✅ Correctly handled output directory creation")
            # Clean up
            if os.path.exists("temp_test_dir"):
                shutil.rmtree("temp_test_dir")
    except Exception as e:
        print(f"  ⚠️  Unexpected error: {e}")
    
    print("✅ Error handling tests passed")


def main():
    """Run all frame extractor tests."""
    print("🚀 Testing Frame Extractor Module")
    print("=" * 50)
    
    tests = [
        test_format_timestamp,
        test_video_info,
        test_frame_extraction,
        test_error_handling
    ]
    
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
        print()
    
    print(f"📊 Tests passed: {passed}/{len(tests)}")
    if passed == len(tests):
        print("🎉 All frame extractor tests passed!")
    else:
        print("⚠️  Some tests failed.")


if __name__ == "__main__":
    main() 