#!/usr/bin/env python3
"""
Test CUDA/GPU device management for backend.
"""
import torch
from clip_loader import get_clip_model

def test_device_management():
    """Test that device management is working correctly."""
    print("🧪 Testing CUDA/GPU Device Management")
    print("=" * 50)
    
    # Test 1: Check if CUDA is available
    print(f"🔍 CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"🚀 GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Test 2: Test device detection
    print(f"\n🎯 Testing Device Detection:")
    try:
        model, tokenizer, preprocess, device = get_clip_model()
        print(f"✅ Device Detection: {device}")
        print(f"✅ Model loaded successfully")
        print(f"✅ Model device: {next(model.parameters()).device}")
        
        # Test 3: Test tensor operations on device
        print(f"\n🧮 Testing Tensor Operations:")
        test_tensor = torch.randn(1, 3, 224, 224).to(device)
        print(f"✅ Test tensor created on {device}")
        print(f"✅ Tensor device: {test_tensor.device}")
        
        # Test 4: Test text encoding
        print(f"\n📝 Testing Text Encoding:")
        test_texts = ["person", "car", "red shirt"]
        text_tokens = tokenizer(test_texts).to(device)
        print(f"✅ Text tokens moved to {device}")
        
        with torch.no_grad():
            text_features = model.encode_text(text_tokens)
        print(f"✅ Text features shape: {text_features.shape}")
        print(f"✅ Text features device: {text_features.device}")
        
        print(f"\n🎉 SUCCESS: CUDA/GPU Device Management is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_device_management()
    if success:
        print("\n✅ Device management test passed!")
    else:
        print("\n❌ Device management test failed!") 
