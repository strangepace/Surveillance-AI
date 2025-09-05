#!/usr/bin/env python3
"""
Utility to check and display analysis results.
"""
import json
from pathlib import Path

def check_results():
    """Check the latest analysis results."""
    results_dir = Path("results")
    
    if not results_dir.exists():
        print("❌ No results directory found")
        return
    
    json_files = list(results_dir.glob("*.json"))
    if not json_files:
        print("❌ No result files found")
        return
    
    # Get the latest result file
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Latest result: {latest_file.name}")
    
    try:
        with open(latest_file, 'r') as f:
            result = json.load(f)
        
        detections = result.get('detections', [])
        alert_summary = result.get('alert_summary', {})
        
        print(f"📊 Total detections: {len(detections)}")
        
        if detections:
            print(f"\n🏆 Top 10 Detections:")
            for i, detection in enumerate(detections[:10], 1):
                timestamp = detection.get('timestamp', 'unknown')
                labels = detection.get('labels', [])
                confidence = detection.get('confidence', 0)
                print(f"{i}. {timestamp} - {confidence:.3f} - {labels}")
        
        if alert_summary:
            print(f"\n🚨 Alert Summary:")
            print(f"   Total: {alert_summary.get('total_detections', 0)}")
            print(f"   Categories: {alert_summary.get('categories', {})}")
            print(f"   Priorities: {alert_summary.get('priorities', {})}")
            
    except Exception as e:
        print(f"❌ Error reading results: {e}")

if __name__ == "__main__":
    check_results() 