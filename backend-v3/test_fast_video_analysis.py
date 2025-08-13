#!/usr/bin/env python3
"""
Fast video analysis test to validate the pipeline with reduced processing.
"""
import requests
import time
from pathlib import Path

def test_fast_video_analysis():
    """Test video analysis with faster processing."""
    print("🚀 Fast Video Analysis Test")
    print("=" * 50)
    
    # Check server
    try:
        response = requests.get('http://127.0.0.1:8003/health', timeout=5)
        print(f"✅ Server: {response.status_code}")
    except:
        print("❌ Server not running")
        return
    
    # Test with naani.mp4 but with shorter timeout
    video_path = Path("content/uploads/naani.mp4")
    if not video_path.exists():
        print("❌ naani.mp4 not found")
        return
    
    print(f"🎥 Testing: naani.mp4")
    print(f"📊 File size: {video_path.stat().st_size / (1024*1024):.1f} MB")
    print(f"🔍 Prompts: 'person, car' (simplified)")
    print(f"⏱️  Timeout: 120s (2 minutes)")
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': ('naani.mp4', f, 'video/mp4')}
            data = {'prompts': 'person, car'}  # Simplified prompts
            
            print("⏳ Starting analysis...")
            start_time = time.time()
            
            response = requests.post(
                'http://127.0.0.1:8003/analyze',
                files=files,
                data=data,
                timeout=120  # 2 minutes
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                detections = result.get('detections', [])
                alert_summary = result.get('alert_summary', {})
                
                print(f"✅ Analysis completed in {processing_time:.1f}s")
                print(f"📊 Detections: {len(detections)}")
                
                if detections:
                    print(f"\n🏆 Detection Results:")
                    for i, detection in enumerate(detections[:5], 1):  # Show top 5
                        timestamp = detection.get('timestamp', 'unknown')
                        labels = detection.get('labels', [])
                        confidence = detection.get('confidence', 0)
                        
                        print(f"{i}. {timestamp} - {confidence:.3f} - {labels}")
                    
                    # Confidence analysis
                    confidences = [d.get('confidence', 0) for d in detections]
                    if confidences:
                        avg_conf = sum(confidences) / len(confidences)
                        max_conf = max(confidences)
                        print(f"\n📈 Confidence: Avg={avg_conf:.3f}, Max={max_conf:.3f}")
                        
                        high_conf = [c for c in confidences if c >= 0.7]
                        print(f"🎯 High confidence (≥0.7): {len(high_conf)} detections")
                else:
                    print("❌ No detections found")
                
                # Show alert summary
                if alert_summary:
                    print(f"\n🚨 Alert Summary:")
                    print(f"   Total: {alert_summary.get('total_detections', 0)}")
                    print(f"   Categories: {alert_summary.get('categories', {})}")
                
                return True
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("⏰ Analysis timed out (120s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_fast_video_analysis()
    if success:
        print("\n🎉 SUCCESS: Fast video analysis test passed!")
    else:
        print("\n⚠️  FAILED: Fast video analysis test failed!")