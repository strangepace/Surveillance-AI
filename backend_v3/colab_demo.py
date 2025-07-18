# backend_v3/colab_demo.py
"""
Colab-ready demo for backend_v3 CLIP integration.
Handles model loading with proper error handling and fallbacks.
"""
import os
import sys
import json
from datetime import datetime

def setup_colab_environment():
    """Setup Colab environment and install dependencies."""
    print("🔧 Setting up Colab environment...")
    
    # Install required packages
    import subprocess
    packages = [
        "open_clip_torch",
        "torch",
        "torchvision", 
        "pillow",
        "opencv-python",
        "pyyaml"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Failed to install {package} (may already be installed)")
    
    print("✅ Environment setup complete")

def test_clip_loading():
    """Test CLIP model loading with error handling."""
    print("🧪 Testing CLIP model loading...")
    
    try:
        # Try to import and load CLIP
        import torch
        import open_clip
        from PIL import Image
        import numpy as np
        
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        
        # Load CLIP model
        model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        tokenizer = open_clip.get_tokenizer('ViT-B-32')
        
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = model.to(device)
        model.eval()
        
        print(f"✅ CLIP model loaded on {device}")
        
        # Test with dummy data
        dummy_img = Image.fromarray(np.uint8(np.random.rand(224, 224, 3) * 255))
        image_input = preprocess(dummy_img).unsqueeze(0).to(device)
        text_input = tokenizer(["test prompt"]).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_input)
        
        print(f"✅ Image features shape: {image_features.shape}")
        print(f"✅ Text features shape: {text_features.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ CLIP loading failed: {e}")
        return False

def create_demo_output():
    """Create a demo output showing the expected format."""
    print("📝 Creating demo output...")
    
    demo_results = [
        {
            "timestamp": "00:02:15",
            "labels": ["elderly man", "white shirt", "blue jacket"],
            "confidence": 0.91,
            "preview_clip": "content/previews/clip_001.mp4",
            "summary": None
        },
        {
            "timestamp": "00:05:30", 
            "labels": ["red car", "vehicle", "moving"],
            "confidence": 0.87,
            "preview_clip": "content/previews/clip_002.mp4",
            "summary": None
        }
    ]
    
    # Save demo output
    output_path = "content/logs/demo_analysis.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(demo_results, f, indent=2)
    
    print(f"✅ Demo output saved to {output_path}")
    return demo_results

def main():
    """Main demo function."""
    print("🚀 Backend-v3 Colab Demo")
    print("=" * 50)
    
    # Setup environment
    setup_colab_environment()
    print()
    
    # Test CLIP loading
    clip_works = test_clip_loading()
    print()
    
    # Create demo output
    demo_results = create_demo_output()
    print()
    
    # Summary
    print("📊 Demo Summary:")
    print(f"  - CLIP Model: {'✅ Working' if clip_works else '❌ Failed'}")
    print(f"  - Demo Output: ✅ Created ({len(demo_results)} events)")
    print(f"  - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if clip_works:
        print("\n🎉 Backend-v3 is ready for development!")
    else:
        print("\n⚠️  CLIP model needs attention, but structure is ready.")

if __name__ == "__main__":
    main() 