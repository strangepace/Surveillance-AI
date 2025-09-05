#!/usr/bin/env python3
"""
Step 2: Confidence Threshold Optimization Test
Tests different similarity thresholds to find optimal values for accurate detections.
"""
import os
import json
import time
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Tuple

class ThresholdOptimizer:
    def __init__(self):
        self.test_videos = [
            ("content/uploads/naani.mp4", ["person, people, man, woman", "car, vehicle"]),
            ("content/uploads/road traffic.mp4", ["car, vehicle, truck", "person, pedestrian"])
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
    
    def start_server(self) -> bool:
        """Start the FastAPI server"""
        import subprocess
        import time
        
        print("🚀 Starting server...")
        try:
            # Start server in background
            process = subprocess.Popen([
                "python", "-m", "uvicorn", "app:app", 
                "--host", "127.0.0.1", "--port", "8007"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test health endpoint
            response = requests.get('http://127.0.0.1:8007/health', timeout=5)
            if response.status_code == 200:
                print("✅ Server started successfully")
                return True
            else:
                print("❌ Server health check failed")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def test_video_analysis(self, video_path: str, prompts: str, threshold: float) -> Dict:
        """Test video analysis with specific threshold"""
        print(f"\n🎬 Testing: {Path(video_path).name}")
        print(f"🔍 Prompts: {prompts}")
        print(f"📊 Threshold: {threshold}")
        
        try:
            with open(video_path, 'rb') as f:
                files = {'file': (Path(video_path).name, f, 'video/mp4')}
                data = {'prompts': prompts}
                
                print("⏳ Starting analysis...")
                start_time = time.time()
                
                response = requests.post(
                    'http://127.0.0.1:8007/analyze',
                    files=files,
                    data=data,
                    timeout=600  # 10 minutes
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
                        print(f"\n🏆 Top 5 Detections:")
                        for i, detection in enumerate(detections[:5], 1):
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
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_threshold_tests(self) -> None:
        """Run tests for all thresholds"""
        print("🧪 THRESHOLD OPTIMIZATION TEST")
        print("=" * 60)
        
        for threshold in self.thresholds:
            print(f"\n{'='*20} THRESHOLD: {threshold} {'='*20}")
            
            # Update config
            self.update_config_threshold(threshold)
            
            # Restart server to pick up new config
            if not self.start_server():
                print("❌ Failed to start server, skipping threshold")
                continue
            
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
                        print(f"❌ {video_name} - {prompts}: Failed")
            
            self.results[threshold] = threshold_results
            
            # Stop server
            try:
                requests.get('http://127.0.0.1:8007/shutdown', timeout=1)
            except:
                pass
    
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
        with open("threshold_optimization_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed results saved to: threshold_optimization_results.json")

def main():
    """Main test function"""
    optimizer = ThresholdOptimizer()
    
    try:
        optimizer.run_threshold_tests()
        optimizer.generate_report()
        
        print(f"\n🎉 Threshold optimization test completed!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main() 