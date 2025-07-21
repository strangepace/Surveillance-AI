# backend_v3/demo_clip_generator.py
"""
Demo script for clip_generator.py module.
Shows how to generate preview clips from detection timestamps.
"""
import os
import tempfile
from .clip_generator import generate_preview_clip, generate_preview_clips_batch, get_clip_info


def main():
    """Demo the clip generator functionality."""
    print("🎬 Clip Generator Demo")
    print("=" * 40)
    
    # Use the naani.mp4 video
    video_path = "../content/uploads/naani.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📹 Using video: {video_path}")
    
    # Create output directory
    output_dir = "preview_clips"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Demo 1: Single clip generation
    print("\n🎯 Demo 1: Single Preview Clip")
    print("-" * 30)
    
    timestamp = "00:01:30"  # 1 minute 30 seconds
    clip_length = 5  # 5 seconds
    
    try:
        clip_path = generate_preview_clip(video_path, output_dir, timestamp, clip_length)
        
        # Get clip info
        clip_info = get_clip_info(clip_path)
        print(f"\n📊 Generated clip info:")
        print(f"   Path: {clip_info['path']}")
        print(f"   Duration: {clip_info['duration']:.2f}s")
        print(f"   Resolution: {clip_info['width']}x{clip_info['height']}")
        print(f"   FPS: {clip_info['fps']:.2f}")
        print(f"   File size: {clip_info['file_size_mb']:.2f}MB")
        
    except Exception as e:
        print(f"❌ Failed to generate single clip: {e}")
    
    # Demo 2: Batch clip generation
    print("\n🎯 Demo 2: Batch Preview Clips")
    print("-" * 30)
    
    timestamps = [
        "00:00:30",  # 30 seconds
        "00:01:00",  # 1 minute
        "00:01:30",  # 1 minute 30 seconds
        "00:02:00"   # 2 minutes
    ]
    
    try:
        clip_paths = generate_preview_clips_batch(video_path, output_dir, timestamps, clip_length=3)
        
        print(f"\n📊 Batch generation results:")
        for i, (timestamp, clip_path) in enumerate(zip(timestamps, clip_paths)):
            if clip_path and os.path.exists(clip_path):
                clip_info = get_clip_info(clip_path)
                print(f"   {i+1}. {timestamp} -> {clip_info['duration']:.2f}s ({clip_info['file_size_mb']:.2f}MB)")
            else:
                print(f"   {i+1}. {timestamp} -> Failed")
                
    except Exception as e:
        print(f"❌ Failed to generate batch clips: {e}")
    
    # Demo 3: Edge cases
    print("\n🎯 Demo 3: Edge Cases")
    print("-" * 30)
    
    edge_timestamps = [
        ("00:00:00", "Start of video"),
        ("00:01:40", "Near end of video"),
        ("00:00:10", "Very short clip")
    ]
    
    for timestamp, description in edge_timestamps:
        try:
            clip_path = generate_preview_clip(video_path, output_dir, timestamp, clip_length=2)
            clip_info = get_clip_info(clip_path)
            print(f"   ✅ {description}: {clip_info['duration']:.2f}s")
        except Exception as e:
            print(f"   ❌ {description}: {e}")
    
    print(f"\n🎉 Demo completed! Check the '{output_dir}' folder for generated clips.")


if __name__ == "__main__":
    main() 