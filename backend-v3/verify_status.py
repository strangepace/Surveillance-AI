# backend_v3/verify_status.py
"""
Quick verification script to check the status of all analyzer pipeline components.
"""
import os
import json
import glob

def check_components():
    """Check if all components are working."""
    print("🔍 Component Status Check")
    print("=" * 30)
    
    # Check 1: Core modules
    modules = [
        'frame_extractor',
        'clip_generator', 
        'prompt_interpreter',
        'analyzer_simple'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}.py - OK")
        except ImportError as e:
            print(f"❌ {module}.py - FAILED: {e}")
    
    # Check 2: Config files
    config_files = [
        'config/clip_config.yaml'
    ]
    
    for config in config_files:
        if os.path.exists(config):
            print(f"✅ {config} - OK")
        else:
            print(f"❌ {config} - MISSING")
    
    # Check 3: Test results
    print("\n📊 Test Results Status:")
    
    # Check test_results directory
    test_dirs = ['test_results', 'pipeline_test_results']
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            files = os.listdir(test_dir)
            json_files = [f for f in files if f.endswith('.json')]
            frame_files = [f for f in files if f.endswith('.jpg')]
            preview_dirs = [d for d in files if d == 'previews']
            
            print(f"  📁 {test_dir}:")
            print(f"    - JSON results: {len(json_files)}")
            print(f"    - Frame images: {len(frame_files)}")
            print(f"    - Preview dirs: {len(preview_dirs)}")
            
            # Check preview clips
            for preview_dir in preview_dirs:
                preview_path = os.path.join(test_dir, preview_dir)
                if os.path.exists(preview_path):
                    preview_files = [f for f in os.listdir(preview_path) if f.endswith('.mp4')]
                    print(f"    - Preview clips: {len(preview_files)}")
        else:
            print(f"  📁 {test_dir}: NOT FOUND")

def check_recent_results():
    """Check the most recent analysis results."""
    print("\n📋 Recent Analysis Results:")
    print("=" * 30)
    
    # Find all JSON result files
    json_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.json') and 'video_' in file:
                json_files.append(os.path.join(root, file))
    
    if json_files:
        # Get the most recent file
        latest_file = max(json_files, key=os.path.getctime)
        print(f"📄 Latest results: {latest_file}")
        
        try:
            with open(latest_file, 'r') as f:
                results = json.load(f)
            
            print(f"📊 Detections found: {len(results)}")
            
            for i, result in enumerate(results[:3]):  # Show first 3
                print(f"  {i+1}. {result.get('timestamp', 'N/A')}: {result.get('labels', [])}")
                print(f"     Confidence: {result.get('confidence', 0):.3f}")
                print(f"     Preview: {result.get('preview_clip', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error reading results: {e}")
    else:
        print("❌ No analysis results found")

def main():
    """Run all checks."""
    print("🚀 Analyzer Pipeline Status Check")
    print("=" * 40)
    
    check_components()
    check_recent_results()
    
    print("\n✅ Status check completed!")

if __name__ == "__main__":
    main() 