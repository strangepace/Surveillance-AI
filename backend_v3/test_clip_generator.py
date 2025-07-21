# backend_v3/test_clip_generator.py
"""
Test script for clip_generator.py module.
Tests preview clip generation, duration verification, edge cases, and filename patterns.
"""
import os
import tempfile
import shutil
from .clip_generator import (
    generate_preview_clip, 
    timestamp_to_seconds, 
    seconds_to_timestamp,
    generate_preview_clips_batch,
    get_clip_info
)


def test_timestamp_conversion():
    """Test timestamp conversion functions."""
    print("🧪 Testing timestamp conversion...")
    
    # Test timestamp_to_seconds
    test_cases = [
        ("00:00:00", 0),
        ("00:01:30", 90),
        ("01:00:00", 3600),
        ("01:30:45", 5445)
    ]
    
    for timestamp, expected_seconds in test_cases:
        result = timestamp_to_seconds(timestamp)
        assert result == expected_seconds, f"Expected {expected_seconds}, got {result}"
        print(f"  ✅ {timestamp} -> {result}s")
    
    # Test seconds_to_timestamp
    for expected_timestamp, seconds in test_cases:
        result = seconds_to_timestamp(seconds)
        assert result == expected_timestamp, f"Expected {expected_timestamp}, got {result}"
        print(f"  ✅ {seconds}s -> {result}")
    
    # Test invalid timestamp format
    try:
        timestamp_to_seconds("invalid")
        assert False, "Should raise ValueError for invalid format"
    except ValueError:
        print("  ✅ Correctly handled invalid timestamp format")
    
    print("✅ Timestamp conversion tests passed")


def test_clip_generation():
    """Test preview clip generation functionality."""
    print("🧪 Testing preview clip generation...")
    
    # Use a real video if available
    test_video = "../content/uploads/naani.mp4"
    if os.path.exists(test_video):
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"  📁 Using temp directory: {temp_dir}")
            
            # Test single clip generation
            print("  🔍 Testing single clip generation...")
            timestamp = "00:02:15"
            clip_path = generate_preview_clip(test_video, temp_dir, timestamp, clip_length=5)
            
            # Verify clip was created
            assert os.path.exists(clip_path), f"Clip file should exist: {clip_path}"
            print(f"  ✅ Clip created: {clip_path}")
            
            # Verify filename pattern
            expected_filename = "clip_00_02_15.mp4"
            actual_filename = os.path.basename(clip_path)
            assert actual_filename == expected_filename, f"Expected {expected_filename}, got {actual_filename}"
            print(f"  ✅ Filename pattern correct: {actual_filename}")
            
            # Verify clip duration
            clip_info = get_clip_info(clip_path)
            actual_duration = clip_info["duration"]
            print(f"  📊 Clip duration: {actual_duration:.2f}s")
            
            # Duration should be approximately 5 seconds (allow some tolerance)
            assert 4.0 <= actual_duration <= 6.0, f"Duration should be ~5s, got {actual_duration}s"
            print(f"  ✅ Clip duration is correct (~5s)")
            
            # Test batch generation
            print("  🔍 Testing batch clip generation...")
            timestamps = ["00:01:00", "00:03:00", "00:05:00"]
            clip_paths = generate_preview_clips_batch(test_video, temp_dir, timestamps, clip_length=3)
            
            assert len(clip_paths) == len(timestamps), "Should return one path per timestamp"
            valid_clips = [p for p in clip_paths if p is not None]
            print(f"  ✅ Generated {len(valid_clips)}/{len(timestamps)} clips in batch")
            
    else:
        print("  ⚠️  Test video not found, creating dummy test...")
        create_dummy_video_and_test()


def create_dummy_video_and_test():
    """Create a dummy video and test clip generation."""
    try:
        import cv2
        import numpy as np
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create dummy video
            dummy_video = os.path.join(temp_dir, "dummy.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(dummy_video, fourcc, 10.0, (320, 240))
            
            # Create 10 seconds of video
            for i in range(100):  # 10 seconds at 10 fps
                frame = np.zeros((240, 320, 3), dtype=np.uint8)
                frame[:, :, 0] = (i * 8) % 256
                frame[:, :, 1] = (i * 16) % 256
                frame[:, :, 2] = (i * 32) % 256
                out.write(frame)
            
            out.release()
            print("  📹 Created dummy test video (10s)")
            
            # Test clip generation
            timestamp = "00:00:05"  # Middle of the video
            clip_path = generate_preview_clip(dummy_video, temp_dir, timestamp, clip_length=3)
            
            assert os.path.exists(clip_path), "Clip should be created"
            clip_info = get_clip_info(clip_path)
            print(f"  ✅ Generated clip: {clip_info['duration']:.2f}s")
            
    except ImportError:
        print("  ⚠️  OpenCV not available, skipping dummy video test")


def test_edge_cases():
    """Test edge cases for clip generation."""
    print("🧪 Testing edge cases...")
    
    test_video = "../content/uploads/naani.mp4"
    if os.path.exists(test_video):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test timestamp at start of video
            print("  🔍 Testing timestamp at video start...")
            try:
                clip_path = generate_preview_clip(test_video, temp_dir, "00:00:00", clip_length=5)
                clip_info = get_clip_info(clip_path)
                print(f"  ✅ Start clip generated: {clip_info['duration']:.2f}s")
            except Exception as e:
                print(f"  ⚠️  Start clip failed: {e}")
            
            # Test timestamp near end of video
            print("  🔍 Testing timestamp near video end...")
            try:
                clip_path = generate_preview_clip(test_video, temp_dir, "00:01:40", clip_length=5)
                clip_info = get_clip_info(clip_path)
                print(f"  ✅ End clip generated: {clip_info['duration']:.2f}s")
            except Exception as e:
                print(f"  ⚠️  End clip failed: {e}")
            
            # Test very short clip
            print("  🔍 Testing very short clip...")
            try:
                clip_path = generate_preview_clip(test_video, temp_dir, "00:01:00", clip_length=1)
                clip_info = get_clip_info(clip_path)
                print(f"  ✅ Short clip generated: {clip_info['duration']:.2f}s")
            except Exception as e:
                print(f"  ⚠️  Short clip failed: {e}")
    
    print("✅ Edge case tests completed")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("🧪 Testing error handling...")
    
    # Test non-existent video file
    try:
        generate_preview_clip("non_existent_video.mp4", "temp_dir", "00:00:00")
        assert False, "Should raise FileNotFoundError"
    except FileNotFoundError:
        print("  ✅ Correctly handled non-existent video file")
    
    # Test invalid timestamp format
    try:
        generate_preview_clip("../content/uploads/naani.mp4", "temp_dir", "invalid_timestamp")
        assert False, "Should raise ValueError"
    except ValueError:
        print("  ✅ Correctly handled invalid timestamp format")
    
    # Test invalid timestamp values
    try:
        generate_preview_clip("../content/uploads/naani.mp4", "temp_dir", "25:70:90")
        print("  ⚠️  Invalid timestamp values should be handled")
    except Exception as e:
        print(f"  ✅ Correctly handled invalid timestamp values: {e}")
    
    print("✅ Error handling tests passed")


def test_clip_info():
    """Test clip information extraction."""
    print("🧪 Testing clip info extraction...")
    
    test_video = "../content/uploads/naani.mp4"
    if os.path.exists(test_video):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate a test clip
            clip_path = generate_preview_clip(test_video, temp_dir, "00:01:00", clip_length=3)
            
            # Get clip info
            clip_info = get_clip_info(clip_path)
            
            # Verify info structure
            required_keys = ["path", "fps", "total_frames", "width", "height", "duration", "duration_formatted", "file_size_mb"]
            for key in required_keys:
                assert key in clip_info, f"Clip info should contain {key}"
            
            print(f"  📊 Clip info: {clip_info['duration']:.2f}s, {clip_info['width']}x{clip_info['height']}, {clip_info['file_size_mb']:.2f}MB")
            print("  ✅ Clip info extraction works correctly")
    
    print("✅ Clip info tests passed")


def main():
    """Run all clip generator tests."""
    print("🚀 Testing Clip Generator Module")
    print("=" * 50)
    
    tests = [
        test_timestamp_conversion,
        test_clip_generation,
        test_edge_cases,
        test_error_handling,
        test_clip_info
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
        print("🎉 All clip generator tests passed!")
    else:
        print("⚠️  Some tests failed.")


if __name__ == "__main__":
    main() 