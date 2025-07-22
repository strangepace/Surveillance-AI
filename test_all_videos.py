#!/usr/bin/env python3
"""
Comprehensive test script for the Surveillance AI backend-v3.
Tests all sample videos with various prompts using the FastAPI /analyze endpoint.
"""

import requests
import json
import time
import os
from pathlib import Path

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/analyze"

# Test videos
VIDEOS = [
    "content/uploads/naani.mp4",
    "content/uploads/road traffic.mp4", 
    "content/uploads/Feds.mp4"
]

# Test prompts for different scenarios
TEST_PROMPTS = [
    # People detection
    "person, people, human, man, woman, child",
    
    # Vehicle detection
    "car, vehicle, truck, motorcycle, bicycle, traffic",
    
    # Activity detection
    "walking, running, standing, sitting, movement",
    
    # Security scenarios
    "suspicious activity, unusual behavior, security threat",
    
    # General surveillance
    "motion, activity, movement, surveillance"
]

def test_health_endpoint():
    """Test the health endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_video_analysis(video_path: str, prompts: str):
    """Test video analysis with given prompts."""
    print(f"\n🎬 Testing video: {video_path}")
    print(f"📝 Prompts: {prompts}")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    try:
        # Prepare the file upload
        with open(video_path, 'rb') as video_file:
            files = {'file': (os.path.basename(video_path), video_file, 'video/mp4')}
            data = {'prompts': prompts}
            
            print("📤 Uploading video and sending analysis request...")
            start_time = time.time()
            
            response = requests.post(ANALYZE_ENDPOINT, files=files, data=data)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis completed in {processing_time:.2f}s")
                print(f"📊 Results: {json.dumps(result, indent=2)}")
                return result
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return None

def main():
    """Main test function."""
    print("🚀 Starting comprehensive video analysis tests...")
    print("=" * 60)
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("❌ Health check failed. Server may not be running.")
        return
    
    print("\n" + "=" * 60)
    print("📹 Testing all sample videos...")
    
    results = {}
    
    # Test each video with different prompt combinations
    for i, video_path in enumerate(VIDEOS, 1):
        print(f"\n{'='*20} Video {i}/{len(VIDEOS)} {'='*20}")
        
        video_results = {}
        
        # Test with different prompt sets
        for j, prompts in enumerate(TEST_PROMPTS, 1):
            print(f"\n--- Test {j}/{len(TEST_PROMPTS)} ---")
            result = test_video_analysis(video_path, prompts)
            video_results[f"test_{j}"] = {
                "prompts": prompts,
                "result": result,
                "success": result is not None
            }
            
            # Small delay between tests
            time.sleep(1)
        
        results[os.path.basename(video_path)] = video_results
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    for video_name, video_results in results.items():
        print(f"\n🎬 {video_name}:")
        successful_tests = sum(1 for test in video_results.values() if test["success"])
        total_tests = len(video_results)
        print(f"   ✅ Successful: {successful_tests}/{total_tests}")
        
        for test_name, test_data in video_results.items():
            status = "✅" if test_data["success"] else "❌"
            print(f"   {status} {test_name}: {test_data['prompts'][:50]}...")
    
    print(f"\n🎉 Testing completed!")
    print(f"📊 Total videos tested: {len(VIDEOS)}")
    print(f"📊 Total tests performed: {len(VIDEOS) * len(TEST_PROMPTS)}")

if __name__ == "__main__":
    main() 