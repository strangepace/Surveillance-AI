# backend_v3/simple_test.py
"""
Simple test script to verify basic backend_v3 structure without requiring PyTorch/CLIP.
"""
import os
import sys
import yaml

def test_config_loading():
    """Test that config files can be loaded."""
    print("Testing config loading...")
    
    # Test YAML loading
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'clip_config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✅ Config loaded: {config}")
        return True
    else:
        print(f"❌ Config file not found: {config_path}")
        return False

def test_directory_structure():
    """Test that required directories exist."""
    print("Testing directory structure...")
    
    required_dirs = [
        'config',
        '../content/previews',
        '../content/model_cache',
        '../content/logs'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if os.path.exists(full_path):
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test that basic imports work."""
    print("Testing imports...")
    
    try:
        from .config_loader import load_clip_config
        print("✅ config_loader imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing backend_v3 basic structure...")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_directory_structure,
        test_imports
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Tests passed: {passed}/{len(tests)}")
    if passed == len(tests):
        print("✅ All basic tests passed!")
    else:
        print("❌ Some tests failed.") 