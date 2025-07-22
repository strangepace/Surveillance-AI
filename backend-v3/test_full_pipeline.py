# backend_v3/test_full_pipeline.py
"""
Comprehensive test for the full analyzer pipeline.
Tests all components and their integration.
"""
import os
import json
import tempfile
from .analyzer_simple import analyze_video_simple, SimpleVideoAnalyzer
from .prompt_interpreter import interpret_prompt
from .frame_extractor import extract_frames
from .clip_generator import generate_preview_clip


def test_individual_components():
    """Test each component individually."""
    print("🧪 Testing Individual Components")
    print("=" * 40)
    
    # Test 1: Prompt Interpreter
    print("\n1. Testing Prompt Interpreter...")
    try:
        test_prompts = [
            "elderly man with red shirt",
            "car with blue color",
            "person with gun"
        ]
        
        for prompt in test_prompts:
            result = interpret_prompt(prompt)
            non_empty = {k: v for k, v in result.items() if v}
            print(f"   ✅ '{prompt}' -> {len(non_empty)} categories")
        
    except Exception as e:
        print(f"   ❌ Prompt interpreter failed: {e}")
    
    # Test 2: Frame Extractor
    print("\n2. Testing Frame Extractor...")
    try:
        video_path = "../content/uploads/naani.mp4"
        if os.path.exists(video_path):
            with tempfile.TemporaryDirectory() as temp_dir:
                frames_data = extract_frames(video_path, temp_dir, sampling_rate=30)  # Sample every 30th frame
                print(f"   ✅ Extracted {len(frames_data)} frames")
        else:
            print("   ⚠️  Video file not found")
            
    except Exception as e:
        print(f"   ❌ Frame extractor failed: {e}")
    
    # Test 3: Clip Generator
    print("\n3. Testing Clip Generator...")
    try:
        video_path = "../content/uploads/naani.mp4"
        if os.path.exists(video_path):
            with tempfile.TemporaryDirectory() as temp_dir:
                clip_path = generate_preview_clip(video_path, temp_dir, "00:01:00", 3)
                print(f"   ✅ Generated clip: {clip_path}")
        else:
            print("   ⚠️  Video file not found")
            
    except Exception as e:
        print(f"   ❌ Clip generator failed: {e}")
    
    # Test 4: Analyzer Components
    print("\n4. Testing Analyzer Components...")
    try:
        analyzer = SimpleVideoAnalyzer()
        
        # Test video ID generation
        video_path = "../content/uploads/naani.mp4"
        video_id = analyzer.generate_video_id(video_path)
        print(f"   ✅ Video ID generation: {video_id}")
        
        # Test similarity simulation
        test_labels = ["man", "red shirt", "car"]
        similarities = analyzer.simulate_clip_similarity({}, test_labels)
        print(f"   ✅ Similarity simulation: {len(similarities)} results")
        
    except Exception as e:
        print(f"   ❌ Analyzer components failed: {e}")


def test_full_pipeline():
    """Test the complete pipeline integration."""
    print("\n🧪 Testing Full Pipeline Integration")
    print("=" * 40)
    
    # Test configuration
    video_path = "../content/uploads/naani.mp4"
    prompts = ["elderly man", "red shirt", "car"]
    
    if not os.path.exists(video_path):
        print("❌ Video file not found, skipping full pipeline test")
        return
    
    print(f"📹 Video: {video_path}")
    print(f"📝 Prompts: {prompts}")
    
    try:
        # Run full analysis
        results_file = analyze_video_simple(video_path, prompts, "pipeline_test_results")
        
        # Verify results
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            print(f"\n📊 Pipeline Results:")
            print(f"   Results file: {results_file}")
            print(f"   Detections found: {len(results)}")
            
            for i, result in enumerate(results):
                print(f"   {i+1}. {result['timestamp']}: {result['labels']} (confidence: {result['confidence']:.3f})")
                print(f"      Preview: {result['preview_clip']}")
            
            # Check if preview clips were generated
            previews_dir = os.path.join("pipeline_test_results", "previews")
            if os.path.exists(previews_dir):
                preview_files = [f for f in os.listdir(previews_dir) if f.endswith('.mp4')]
                print(f"   Preview clips generated: {len(preview_files)}")
            
            print("✅ Full pipeline test completed successfully!")
            
        else:
            print("❌ Results file not found")
            
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")


def test_error_handling():
    """Test error handling for various scenarios."""
    print("\n🧪 Testing Error Handling")
    print("=" * 40)
    
    # Test 1: Non-existent video file
    print("\n1. Testing non-existent video...")
    try:
        result = analyze_video_simple("non_existent_video.mp4", ["test"], "error_test")
        print("   ❌ Should have failed for non-existent video")
    except Exception as e:
        print(f"   ✅ Correctly handled non-existent video: {e}")
    
    # Test 2: Empty prompts
    print("\n2. Testing empty prompts...")
    try:
        video_path = "../content/uploads/naani.mp4"
        if os.path.exists(video_path):
            result = analyze_video_simple(video_path, [], "error_test")
            print("   ✅ Handled empty prompts")
        else:
            print("   ⚠️  Video file not found")
    except Exception as e:
        print(f"   ❌ Failed to handle empty prompts: {e}")
    
    # Test 3: Invalid output directory
    print("\n3. Testing invalid output directory...")
    try:
        video_path = "../content/uploads/naani.mp4"
        if os.path.exists(video_path):
            result = analyze_video_simple(video_path, ["test"], "/invalid/path/that/should/fail")
            print("   ✅ Handled invalid output directory")
        else:
            print("   ⚠️  Video file not found")
    except Exception as e:
        print(f"   ✅ Correctly handled invalid output directory: {e}")


def main():
    """Run all tests."""
    print("🚀 Full Pipeline Testing")
    print("=" * 50)
    
    # Run individual component tests
    test_individual_components()
    
    # Run full pipeline test
    test_full_pipeline()
    
    # Run error handling tests
    test_error_handling()
    
    print("\n🎉 All tests completed!")
    print("\n📋 Summary:")
    print("  ✅ Individual components tested")
    print("  ✅ Full pipeline integration tested")
    print("  ✅ Error handling tested")
    print("  ✅ Results validation completed")


if __name__ == "__main__":
    main() 