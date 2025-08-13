#!/usr/bin/env python3
"""
Test Google Model Routing
Tests the model parameter routing with Google Video Intelligence.
"""
import os
import requests
import time
from pathlib import Path

def test_google_model():
    """Test Google model routing"""
    print("🧪 GOOGLE MODEL ROUTING TEST")
    print("=" * 40)
    
    # Test video and prompts
    video_path = "content/uploads/naani.mp4"
    prompts = "person, car, red shirt"
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return False
    
    print(f"📹 Testing video: {Path(video_path).name}")
    print(f"🔍 Prompts: {prompts}")
    print(f"🤖 Model: google")
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (Path(video_path).name, f, 'video/mp4')}
            data = {'prompts': prompts, 'model': 'google'}
            
            print("⏳ Starting Google analysis...")
            start_time = time.time()
            
            response = requests.post(
                'http://127.0.0.1:8008/analyze',
                files=files,
                data=data,
                timeout=60  # 1 minute timeout for placeholder
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                detections = result.get('results', [])
                
                print(f"✅ Google analysis completed in {processing_time:.1f}s")
                print(f"📊 Detections: {len(detections)}")
                print(f"📋 Video ID: {result.get('video_id', 'unknown')}")
                
                return True
            else:
                print(f"❌ Google analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Google analysis timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    try:
        success = test_google_model()
        
        if success:
            print(f"\n🎉 GOOGLE MODEL TEST PASSED!")
            print("✅ Model routing works correctly")
        else:
            print(f"\n❌ GOOGLE MODEL TEST FAILED!")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main() 