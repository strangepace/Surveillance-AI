#!/usr/bin/env python3
"""
Fast Threshold Optimization Test
Tests different similarity thresholds with longer timeout and better progress tracking.
"""
import os
import json
import time
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Tuple

class FastThresholdOptimizer:
    def __init__(self):
        self.test_videos = [
            ("content/uploads/naani.mp4", ["person"]),  # Single prompt for speed
        ]
        self.thresholds = [0.2, 0.3, 0.5, 0.7]
        self.results = {}
        
    def update_config_threshold(self, threshold: float) -> None:
        """Update the threshold in clip_config.yaml"""
        config_path = "config/clip_config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        config['similarity_threshold'] = threshold
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"✅ Updated threshold to {threshold}")
    
    def test_video_analysis(self, video_path: str, prompts: str, threshold: float) -> Dict:
        """Test video analysis with specific threshold"""
        print(f"\n🎬 Testing: {Path(video_path).name}")
        print(f"🔍 Prompts: {prompts}")
        print(f"📊 Threshold: {threshold}")
        
        # Check if video exists
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            return {'success': False, 'error': 'Video file not found'}
        
        try:
            with open(video_path, 'rb') as f:
                files = {'file': (Path(video_path).name, f, 'video/mp4')}
                data = {'prompts': prompts}
                
                print("⏳ Starting analysis (300s timeout)...")
                start_time = time.time()
                
                response = requests.post(
                    'http://127.0.0.1:8007/analyze',
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes timeout
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    detections = result.get('results', [])
                    
                    print(f"✅ Analysis completed in {processing_time:.1f}s")
                    print(f"📊 Detections: {len(detections)}")
                    
                    # Analyze detections
                    confidence_scores = []
                    detection_summary = []
                    
                    for detection in detections:
                        confidence = detection.get('confidence', 0)
                        labels = detection.get('labels', [])
                        timestamp = detection.get('timestamp', 'unknown')
                        
                        confidence_scores.append(confidence)
                        detection_summary.append({
                            'timestamp': timestamp,
                            'labels': labels,
                            'confidence': confidence
                        })
                    
                    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                    max_confidence = max(confidence_scores) if confidence_scores else 0
                    
                    print(f"📈 Average confidence: {avg_confidence:.3f}")
                    print(f"🏆 Max confidence: {max_confidence:.3f}")
                    
                    if detections:
                        print(f"\n🏆 Top 3 Detections:")
                        for i, detection in enumerate(detections[:3], 1):
                            timestamp = detection.get('timestamp', 'unknown')
                            labels = detection.get('labels', [])
                            confidence = detection.get('confidence', 0)
                            print(f"{i}. {timestamp} - {confidence:.3f} - {labels}")
                    
                    return {
                        'success': True,
                        'detections_count': len(detections),
                        'avg_confidence': avg_confidence,
                        'max_confidence': max_confidence,
                        'processing_time': processing_time,
                        'detection_summary': detection_summary,
                        'all_confidence_scores': confidence_scores
                    }
                else:
                    print(f"❌ Failed: {response.status_code}")
                    print(f"Error: {response.text}")
                    return {'success': False, 'error': response.text}
                    
        except requests.exceptions.Timeout:
            print("❌ Analysis timed out (300s)")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_threshold_tests(self) -> None:
        """Run tests for all thresholds"""
        print("🧪 FAST THRESHOLD OPTIMIZATION TEST")
        print("=" * 60)
        
        for threshold in self.thresholds:
            print(f"\n{'='*20} THRESHOLD: {threshold} {'='*20}")
            
            # Update config
            self.update_config_threshold(threshold)
            
            # Wait a moment for config to be read
            time.sleep(2)
            
            threshold_results = {}
            
            for video_path, prompts_list in self.test_videos:
                video_name = Path(video_path).name
                print(f"\n📹 Testing video: {video_name}")
                
                for prompts in prompts_list:
                    result = self.test_video_analysis(video_path, prompts, threshold)
                    threshold_results[f"{video_name}_{prompts}"] = result
                    
                    if result['success']:
                        print(f"✅ {video_name} - {prompts}: {result['detections_count']} detections, avg: {result['avg_confidence']:.3f}")
                    else:
                        print(f"❌ {video_name} - {prompts}: Failed - {result.get('error', 'Unknown error')}")
            
            self.results[threshold] = threshold_results
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        print(f"\n{'='*60}")
        print("📊 THRESHOLD OPTIMIZATION REPORT")
        print("=" * 60)
        
        # Summary table
        print(f"\n📋 SUMMARY TABLE:")
        print(f"{'Threshold':<10} {'Detections':<12} {'Avg Conf':<10} {'Max Conf':<10} {'Status':<10}")
        print("-" * 60)
        
        for threshold in self.thresholds:
            if threshold in self.results:
                total_detections = 0
                all_confidences = []
                
                for test_name, result in self.results[threshold].items():
                    if result['success']:
                        total_detections += result['detections_count']
                        all_confidences.extend(result['all_confidence_scores'])
                
                avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0
                max_conf = max(all_confidences) if all_confidences else 0
                
                status = "✅ GOOD" if avg_conf > 0.5 else "⚠️ LOW" if avg_conf > 0.3 else "❌ POOR"
                
                print(f"{threshold:<10} {total_detections:<12} {avg_conf:<10.3f} {max_conf:<10.3f} {status:<10}")
        
        # Detailed analysis
        print(f"\n🔍 DETAILED ANALYSIS:")
        for threshold in self.thresholds:
            if threshold in self.results:
                print(f"\n📊 Threshold {threshold}:")
                for test_name, result in self.results[threshold].items():
                    if result['success']:
                        print(f"  {test_name}: {result['detections_count']} detections, avg: {result['avg_confidence']:.3f}")
                    else:
                        print(f"  {test_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        best_threshold = None
        best_score = 0
        
        for threshold in self.thresholds:
            if threshold in self.results:
                total_detections = 0
                all_confidences = []
                
                for test_name, result in self.results[threshold].items():
                    if result['success']:
                        total_detections += result['detections_count']
                        all_confidences.extend(result['all_confidence_scores'])
                
                if all_confidences:
                    avg_conf = sum(all_confidences) / len(all_confidences)
                    # Score based on detection count and confidence
                    score = total_detections * avg_conf
                    
                    if score > best_score:
                        best_score = score
                        best_threshold = threshold
        
        if best_threshold:
            print(f"🎯 Recommended threshold: {best_threshold}")
            print(f"   - Provides good balance of detections and confidence")
            print(f"   - Score: {best_score:.2f}")
        else:
            print("❌ No optimal threshold found")
        
        # Save detailed results
        with open("fast_threshold_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed results saved to: fast_threshold_results.json")

def main():
    """Main test function"""
    optimizer = FastThresholdOptimizer()
    
    try:
        optimizer.run_threshold_tests()
        optimizer.generate_report()
        
        print(f"\n🎉 Fast threshold optimization test completed!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main() 