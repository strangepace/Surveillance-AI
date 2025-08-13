#!/usr/bin/env python3
"""
Simple test for CUDA/GPU device detection.
"""
import torch

def test_cuda_detection():
    """Test basic CUDA detection."""
    print("🧪 Simple CUDA/GPU Detection Test")
    print("=" * 40)
    
    # Check CUDA availability
    cuda_available = torch.cuda.is_available()
    print(f"🔍 CUDA Available: {cuda_available}")
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"🚀 GPU Name: {gpu_name}")
        print(f"📊 GPU Memory: {gpu_memory:.1f} GB")
        print(f"✅ CUDA/GPU detection working correctly!")
    else:
        print(f"🖥️  Running on CPU")
        print(f"✅ CPU fallback working correctly!")
    
    return True

if __name__ == "__main__":
    test_cuda_detection() 