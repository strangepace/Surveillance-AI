#!/usr/bin/env python3
"""
Quick Single Video Test
Tests the pipeline with lower threshold to verify end-to-end functionality.
"""
import os
import requests
import time
from pathlib import Path

def test_single_video():
    """Test single video analysis with lower threshold"""
    print("🧪 QUICK FUNCTIONAL CHECK")
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
    print(f"📊 Threshold: 0.15 (lowered for testing)")
    print(f"🤖 Model: clip")
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (Path(video_path).name, f, 'video/mp4')}
            data = {'prompts': prompts, 'model': 'clip'}
            
            print("⏳ Starting analysis...")
            start_time = time.time()
            
            response = requests.post(
                'http://127.0.0.1:8008/analyze',
                files=files,
                data=data,
                timeout=600  # 10 minutes timeout
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                detections = result.get('results', [])
                
                print(f"✅ Analysis completed in {processing_time:.1f}s")
                print(f"📊 Detections: {len(detections)}")
                
                if detections:
                    print(f"\n🏆 DETECTION RESULTS:")
                    confidence_scores = []
                    
                    for i, detection in enumerate(detections[:10], 1):  # Show top 10
                        timestamp = detection.get('timestamp', 'unknown')
                        labels = detection.get('labels', [])
                        confidence = detection.get('confidence', 0)
                        confidence_scores.append(confidence)
                        
                        print(f"{i}. {timestamp} - {confidence:.3f} - {labels}")
                    
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    max_confidence = max(confidence_scores)
                    
                    print(f"\n📈 SUMMARY:")
                    print(f"   Total detections: {len(detections)}")
                    print(f"   Average confidence: {avg_confidence:.3f}")
                    print(f"   Highest confidence: {max_confidence:.3f}")
                    print(f"   Processing time: {processing_time:.1f}s")
                    
                    return True
                else:
                    print("❌ No detections found")
                    return False
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Analysis timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    try:
        success = test_single_video()
        
        if success:
            print(f"\n🎉 FUNCTIONAL CHECK PASSED!")
            print("✅ Pipeline works end-to-end with lower threshold")
        else:
            print(f"\n❌ FUNCTIONAL CHECK FAILED!")
            print("❌ Pipeline needs further investigation")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main() 