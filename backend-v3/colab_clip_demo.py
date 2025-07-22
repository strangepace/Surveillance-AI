# backend_v3/colab_clip_demo.py
"""
Colab-compatible demo for clip_generator.py module.
Can be run in Google Colab environment with uploaded videos.
"""
import os
import cv2
import tempfile
from .clip_generator import generate_preview_clip, generate_preview_clips_batch, get_clip_info


def colab_clip_demo(video_path: str = None, output_dir: str = "preview_clips"):
    """
    Demo the clip generator functionality in Colab environment.
    
    Args:
        video_path (str): Path to video file (if None, will look for uploaded files)
        output_dir (str): Directory to save preview clips
    """
    print("🎬 Colab Clip Generator Demo")
    print("=" * 40)
    
    # In Colab, look for uploaded videos if no path provided
    if video_path is None:
        # Common upload locations in Colab
        possible_paths = [
            "/content/naani.mp4",
            "/content/video.mp4", 
            "/content/uploads/naani.mp4",
            "naani.mp4",
            "video.mp4"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                video_path = path
                break
        else:
            print("❌ No video file found. Please upload a video file to Colab.")
            print("   Supported paths: /content/naani.mp4, /content/video.mp4, etc.")
            return
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📹 Using video: {video_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Get video info
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()
    
    print(f"📊 Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
    
    # Demo 1: Single clip generation
    print("\n🎯 Demo 1: Single Preview Clip")
    print("-" * 30)
    
    # Calculate a timestamp in the middle of the video
    mid_time = int(duration / 2)
    timestamp = f"{mid_time//3600:02d}:{(mid_time%3600)//60:02d}:{mid_time%60:02d}"
    
    try:
        clip_path = generate_preview_clip(video_path, output_dir, timestamp, clip_length=5)
        clip_info = get_clip_info(clip_path)
        
        print(f"✅ Generated clip at {timestamp}:")
        print(f"   Path: {clip_info['path']}")
        print(f"   Duration: {clip_info['duration']:.2f}s")
        print(f"   Resolution: {clip_info['width']}x{clip_info['height']}")
        print(f"   File size: {clip_info['file_size_mb']:.2f}MB")
        
    except Exception as e:
        print(f"❌ Failed to generate single clip: {e}")
    
    # Demo 2: Multiple clips at different timestamps
    print("\n🎯 Demo 2: Multiple Preview Clips")
    print("-" * 30)
    
    # Generate timestamps at different points in the video
    timestamps = []
    for i in range(1, 5):  # 4 clips
        time_point = int(duration * i / 5)  # Distribute evenly
        timestamp = f"{time_point//3600:02d}:{(time_point%3600)//60:02d}:{time_point%60:02d}"
        timestamps.append(timestamp)
    
    try:
        clip_paths = generate_preview_clips_batch(video_path, output_dir, timestamps, clip_length=3)
        
        print(f"📊 Generated {len([p for p in clip_paths if p])} clips:")
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
        (f"{int(duration)//3600:02d}:{(int(duration)%3600)//60:02d}:{int(duration)%60:02d}", "End of video"),
        ("00:00:10", "Early in video")
    ]
    
    for timestamp, description in edge_timestamps:
        try:
            clip_path = generate_preview_clip(video_path, output_dir, timestamp, clip_length=2)
            clip_info = get_clip_info(clip_path)
            print(f"   ✅ {description}: {clip_info['duration']:.2f}s")
        except Exception as e:
            print(f"   ❌ {description}: {e}")
    
    # List all generated clips
    print(f"\n📁 Generated clips in '{output_dir}':")
    if os.path.exists(output_dir):
        clips = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
        for clip in sorted(clips):
            clip_path = os.path.join(output_dir, clip)
            size_mb = os.path.getsize(clip_path) / (1024 * 1024)
            print(f"   📹 {clip} ({size_mb:.2f}MB)")
    
    print(f"\n🎉 Demo completed! Check the '{output_dir}' folder for generated clips.")


def upload_video_to_colab():
    """Helper function to upload video in Colab."""
    try:
        from google.colab import files
        uploaded = files.upload()
        for filename in uploaded.keys():
            print(f"📁 Uploaded: {filename}")
        return list(uploaded.keys())[0] if uploaded else None
    except ImportError:
        print("⚠️  Not running in Colab environment")
        return None


# Example usage in Colab:
if __name__ == "__main__":
    # For Colab usage, uncomment the following lines:
    # video_file = upload_video_to_colab()
    # if video_file:
    #     colab_clip_demo(video_file)
    
    # For local testing:
    colab_clip_demo() 