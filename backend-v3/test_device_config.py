#!/usr/bin/env python3
"""
Test device configuration without loading CLIP model.
"""
import torch
import yaml

def test_device_config():
    """Test device configuration logic."""
    print("🧪 Testing Device Configuration Logic")
    print("=" * 50)
    
    # Load config
    with open("config/clip_config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    device_config = config.get('device', {})
    auto_detect = device_config.get('auto_detect', True)
    force_cpu = device_config.get('force_cpu', False)
    log_device = device_config.get('log_device', True)
    
    print(f"📋 Config loaded:")
    print(f"   auto_detect: {auto_detect}")
    print(f"   force_cpu: {force_cpu}")
    print(f"   log_device: {log_device}")
    
    # Test device selection logic
    print(f"\n🎯 Device Selection Logic:")
    print(f"   CUDA Available: {torch.cuda.is_available()}")
    
    if force_cpu:
        selected_device = 'cpu'
        print(f"   Force CPU: {selected_device}")
    elif auto_detect and torch.cuda.is_available():
        selected_device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        print(f"   Auto-detect GPU: {selected_device} ({gpu_name})")
    else:
        selected_device = 'cpu'
        print(f"   Fallback to CPU: {selected_device}")
    
    # Log device selection
    if log_device:
        if selected_device == 'cuda':
            gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unknown'
            print(f"🚀 Using device: {selected_device} ({gpu_name})")
        else:
            print(f"🖥️  Using device: {selected_device}")
    
    print(f"\n✅ Device configuration test completed!")
    return True

if __name__ == "__main__":
    test_device_config() 