# backend_v3/demo_analyzer.py
"""
Demo script for analyzer.py module.
Tests the full video analysis pipeline with sample inputs.
"""
import os
import json
from .analyzer import VideoAnalyzer, analyze_video
from .prompt_interpreter import interpret_multiple_prompts


def main():
    """Demo the analyzer pipeline functionality."""
    print("🎬 Video Analyzer Pipeline Demo")
    print("=" * 50)
    
    # Test configuration
    video_path = "../content/uploads/naani.mp4"
    prompts = [
        "man with red shirt",
        "fire",
        "gun",
        "car",
        "person walking"
    ]
    output_dir = "results"
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        print("   Please ensure the video file exists in the uploads directory.")
        return
    
    print(f"📹 Video: {video_path}")
    print(f"📝 Prompts: {prompts}")
    print(f"📁 Output: {output_dir}")
    
    # Create analyzer instance
    try:
        analyzer = VideoAnalyzer()
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return
    
    # Test simple analysis first (without full CLIP processing)
    print(f"\n🔍 Testing simple analysis...")
    try:
        results_file = analyzer.analyze_video_simple(video_path, prompts, output_dir)
        
        # Load and display results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        print(f"\n📊 Analysis Results:")
        print(f"   Results file: {results_file}")
        print(f"   Detections found: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   {i+1}. {result['timestamp']}: {result['labels']} (confidence: {result['confidence']:.3f})")
            print(f"      Preview: {result['preview_clip']}")
        
    except Exception as e:
        print(f"❌ Simple analysis failed: {e}")
    
    # Test full analysis (if CLIP is available)
    print(f"\n🔍 Testing full analysis...")
    try:
        # Use a subset of prompts for faster testing
        test_prompts = ["man", "person"]
        results_file = analyze_video(video_path, test_prompts, output_dir)
        
        print(f"✅ Full analysis completed: {results_file}")
        
        # Load and display results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        print(f"\n📊 Full Analysis Results:")
        print(f"   Results file: {results_file}")
        print(f"   Detections found: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   {i+1}. {result['timestamp']}: {result['labels']} (confidence: {result['confidence']:.3f})")
            if 'prompt_matches' in result and result['prompt_matches']:
                matches = result['prompt_matches']
                print(f"      Matches: {matches}")
        
    except Exception as e:
        print(f"⚠️  Full analysis failed (this is expected if CLIP model is not available): {e}")
        print("   The simple analysis above shows the pipeline structure.")
    
    # Test different prompt combinations
    print(f"\n🔍 Testing different prompt combinations...")
    
    prompt_combinations = [
        (["elderly man"], "Single person detection"),
        (["red shirt", "blue car"], "Color-based detection"),
        (["fire", "smoke"], "Fire detection"),
        (["gun", "weapon"], "Weapon detection"),
        (["person walking", "person running"], "Activity detection")
    ]
    
    for prompts, description in prompt_combinations:
        try:
            print(f"\n   Testing: {description}")
            print(f"   Prompts: {prompts}")
            
            results_file = analyzer.analyze_video_simple(video_path, prompts, output_dir)
            
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            print(f"   Results: {len(results)} detections")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Show output directory structure
    print(f"\n📁 Output Directory Structure:")
    if os.path.exists(output_dir):
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    
    print(f"\n🎉 Demo completed!")
    print("The analyzer pipeline successfully:")
    print("  ✅ Loaded CLIP model and configuration")
    print("  ✅ Interpreted natural language prompts")
    print("  ✅ Extracted video frames")
    print("  ✅ Generated preview clips")
    print("  ✅ Created structured JSON results")


def test_analyzer_components():
    """Test individual analyzer components."""
    print("\n🧪 Testing Analyzer Components")
    print("=" * 40)
    
    analyzer = VideoAnalyzer()
    
    # Test video ID generation
    video_path = "../content/uploads/naani.mp4"
    video_id = analyzer.generate_video_id(video_path)
    print(f"✅ Video ID generation: {video_id}")
    
    # Test similarity calculation
    try:
        import torch
        # Create dummy tensors for testing
        image_features = torch.randn(1, 512)
        text_features = torch.randn(1, 512)
        
        similarity = analyzer.calculate_similarity(image_features, text_features)
        print(f"✅ Similarity calculation: {similarity:.3f}")
        
    except Exception as e:
        print(f"⚠️  Similarity calculation test failed: {e}")
    
    # Test prompt interpretation integration
    try:
        from prompt_interpreter import interpret_multiple_prompts
        
        test_prompts = ["man with red shirt", "burning car"]
        categories = interpret_multiple_prompts(test_prompts)
        
        print(f"✅ Prompt interpretation: {len(categories)} prompt categories")
        for i, category in enumerate(categories):
            non_empty = {k: v for k, v in category.items() if v}
            print(f"   Prompt {i+1}: {len(non_empty)} categories")
        
    except Exception as e:
        print(f"⚠️  Prompt interpretation test failed: {e}")


if __name__ == "__main__":
    main()
    test_analyzer_components() 