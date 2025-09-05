#!/usr/bin/env python3
"""
Comprehensive test script to validate backend with real test videos.
Tests naani.mp4 and Feds.mp4 with meaningful prompts.
"""
import requests
import time
import json
from pathlib import Path

def test_video_analysis(video_path: str, prompts: str, video_name: str):
    """Test a single video with specific prompts."""
    print(f"\n🎬 Testing {video_name}")
    print("=" * 60)
    
    # Check if video exists
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        return None
    
    print(f"📁 Video: {video_path}")
    print(f"📊 File size: {Path(video_path).stat().st_size / (1024*1024):.1f} MB")
    print(f"🔍 Prompts: '{prompts}'")
    print(f"🎯 Threshold: 0.2 (current config)")
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (Path(video_path).name, f, 'video/mp4')}
            data = {'prompts': prompts}
            
            print("⏳ Starting analysis...")
            start_time = time.time()
            
            response = requests.post(
                'http://127.0.0.1:8003/analyze',
                files=files,
                data=data,
                timeout=600  # 10 minutes
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                detections = result.get('detections', [])
                alert_summary = result.get('alert_summary', {})
                
                print(f"✅ Analysis completed in {processing_time:.1f}s")
                print(f"📊 Total detections: {len(detections)}")
                
                # Show detection details
                if detections:
                    print(f"\n🏆 Detection Results:")
                    print("-" * 50)
                    
                    confidences = []
                    for i, detection in enumerate(detections, 1):
                        timestamp = detection.get('timestamp', 'unknown')
                        labels = detection.get('labels', [])
                        confidence = detection.get('confidence', 0)
                        preview_clip = detection.get('preview_clip', 'N/A')
                        alert_class = detection.get('alert_classification', {})
                        
                        confidences.append(confidence)
                        
                        print(f"{i}. {timestamp} - Confidence: {confidence:.3f}")
                        print(f"   Labels: {labels}")
                        print(f"   Preview: {preview_clip}")
                        if alert_class:
                            primary_category = alert_class.get('primary_category', 'general')
                            priority = alert_class.get('priority', 'low')
                            print(f"   Alert: {primary_category} ({priority} priority)")
                        print()
                    
                    # Confidence statistics
                    if confidences:
                        avg_conf = sum(confidences) / len(confidences)
                        max_conf = max(confidences)
                        min_conf = min(confidences)
                        print(f"📈 Confidence Statistics:")
                        print(f"   Average: {avg_conf:.3f}")
                        print(f"   Maximum: {max_conf:.3f}")
                        print(f"   Minimum: {min_conf:.3f}")
                        print(f"   Range: {min_conf:.3f} - {max_conf:.3f}")
                        
                        # High confidence detections
                        high_conf = [c for c in confidences if c >= 0.7]
                        medium_conf = [c for c in confidences if 0.4 <= c < 0.7]
                        low_conf = [c for c in confidences if c < 0.4]
                        
                        print(f"\n🎯 Confidence Distribution:")
                        print(f"   High (≥0.7): {len(high_conf)} detections")
                        print(f"   Medium (0.4-0.7): {len(medium_conf)} detections")
                        print(f"   Low (<0.4): {len(low_conf)} detections")
                else:
                    print("❌ No detections found")
                
                # Show alert summary
                if alert_summary:
                    print(f"\n🚨 Alert Summary:")
                    print(f"   Total: {alert_summary.get('total_detections', 0)}")
                    print(f"   Categories: {alert_summary.get('categories', {})}")
                    print(f"   Priorities: {alert_summary.get('priorities', {})}")
                
                return {
                    'success': True,
                    'detections': detections,
                    'processing_time': processing_time,
                    'alert_summary': alert_summary
                }
                
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"Error: {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Run comprehensive video analysis tests."""
    print("🎯 backend Comprehensive Video Analysis Test")
    print("=" * 70)
    
    # Check server status
    try:
        response = requests.get('http://127.0.0.1:8003/health', timeout=5)
        print(f"✅ Server: {response.status_code} - {response.json()}")
    except:
        print("❌ Server not running. Please start the server first.")
        return
    
    # Test videos and prompts
    test_cases = [
        {
            'video_path': 'content/uploads/naani.mp4',
            'prompts': 'person, car, yellow flowers, water, airplane',
            'video_name': 'naani.mp4 (Family Video)'
        },
        {
            'video_path': 'content/uploads/Feds.mp4', 
            'prompts': 'soldier, gun, smoke, reporter, cop car',
            'video_name': 'Feds.mp4 (Media Riot)'
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        result = test_video_analysis(
            test_case['video_path'],
            test_case['prompts'], 
            test_case['video_name']
        )
        results[test_case['video_name']] = result
    
    # Summary report
    print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    
    total_detections = 0
    total_processing_time = 0
    successful_tests = 0
    
    for video_name, result in results.items():
        if result['success']:
            successful_tests += 1
            detections = result['detections']
            processing_time = result['processing_time']
            
            total_detections += len(detections)
            total_processing_time += processing_time
            
            print(f"\n✅ {video_name}:")
            print(f"   Detections: {len(detections)}")
            print(f"   Processing time: {processing_time:.1f}s")
            
            if detections:
                confidences = [d.get('confidence', 0) for d in detections]
                avg_conf = sum(confidences) / len(confidences)
                print(f"   Avg confidence: {avg_conf:.3f}")
        else:
            print(f"\n❌ {video_name}:")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Successful tests: {successful_tests}/{len(test_cases)}")
    print(f"   Total detections: {total_detections}")
    print(f"   Total processing time: {total_processing_time:.1f}s")
    
    if successful_tests == len(test_cases):
        print(f"\n🎉 SUCCESS: All tests passed!")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS: {successful_tests}/{len(test_cases)} tests passed")

if __name__ == "__main__":
    main()
