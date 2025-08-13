#!/usr/bin/env python3
"""
Quick verification test to ensure the system is working properly.
"""
import os
import requests
import time
from pathlib import Path

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get('http://127.0.0.1:8007/health', timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_simple_analysis():
    """Test simple video analysis with short timeout"""
    print("\n🎬 Testing simple video analysis...")
    
    # Check if test video exists
    video_path = "content/uploads/naani.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Test video not found: {video_path}")
        return False
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': ('naani.mp4', f, 'video/mp4')}
            data = {'prompts': 'person'}
            
            print("⏳ Starting analysis (30s timeout)...")
            start_time = time.time()
            
            response = requests.post(
                'http://127.0.0.1:8007/analyze',
                files=files,
                data=data,
                timeout=30  # 30 seconds timeout
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                detections = result.get('results', [])
                
                print(f"✅ Analysis completed in {processing_time:.1f}s")
                print(f"📊 Detections: {len(detections)}")
                
                if detections:
                    print(f"\n🏆 Top 3 Detections:")
                    for i, detection in enumerate(detections[:3], 1):
                        timestamp = detection.get('timestamp', 'unknown')
                        labels = detection.get('labels', [])
                        confidence = detection.get('confidence', 0)
                        print(f"{i}. {timestamp} - {confidence:.3f} - {labels}")
                
                return True
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Analysis timed out (30s)")
        return False
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

def main():
    """Main verification function"""
    print("🧪 QUICK VERIFICATION TEST")
    print("=" * 40)
    
    # Test 1: Health check
    if not test_health():
        print("❌ Health check failed - server may not be running")
        return
    
    # Test 2: Simple analysis
    if test_simple_analysis():
        print("\n🎉 All tests passed! System is working properly.")
    else:
        print("\n⚠️ Analysis test failed - may need longer timeout or different video")

if __name__ == "__main__":
    main() 