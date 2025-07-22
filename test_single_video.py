#!/usr/bin/env python3
"""
Simple test script to test one video analysis.
"""

import requests
import json
import os

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/analyze"

def test_single_video():
    """Test analysis of a single video."""
    video_path = "content/uploads/naani.mp4"
    prompts = "person, people"
    
    print(f"🎬 Testing video: {video_path}")
    print(f"📝 Prompts: {prompts}")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    try:
        # Prepare the file upload
        with open(video_path, 'rb') as video_file:
            files = {'file': (os.path.basename(video_path), video_file, 'video/mp4')}
            data = {'prompts': prompts}
            
            print("📤 Uploading video and sending analysis request...")
            
            response = requests.post(ANALYZE_ENDPOINT, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis completed successfully!")
                print(f"📊 Results: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Analysis error: {e}")

if __name__ == "__main__":
    test_single_video() 