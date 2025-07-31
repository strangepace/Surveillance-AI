#!/usr/bin/env python3
"""
Error Handling Test for Surveillance AI Backend-v3
Tests various error scenarios and validates error responses.
"""
import os
import requests
import time
import json
from pathlib import Path

def test_invalid_file_type():
    """Test uploading invalid file type."""
    print("🧪 Testing invalid file type...")
    
    # Create a text file (invalid)
    test_file = "test_invalid.txt"
    with open(test_file, "w") as f:
        f.write("This is not a video file")
    
    try:
        with open(test_file, "rb") as f:
            files = {'file': (test_file, f, 'text/plain')}
            data = {'prompts': 'person, car', 'model': 'clip'}
            
            response = requests.post(
                'http://127.0.0.1:8008/analyze',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 400:
                result = response.json()
                if result.get("status") == "error" and "validation" in result.get("error_type", ""):
                    print("✅ Invalid file type correctly rejected")
                    return True
                else:
                    print(f"❌ Unexpected error response: {result}")
                    return False
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_empty_prompts():
    """Test with empty prompts."""
    print("🧪 Testing empty prompts...")
    
    # Create a valid video file
    test_file = "test_video.mp4"
    with open(test_file, "wb") as f:
        f.write(b"fake video data")
    
    try:
        with open(test_file, "rb") as f:
            files = {'file': (test_file, f, 'video/mp4')}
            data = {'prompts': '', 'model': 'clip'}  # Empty prompts
            
            response = requests.post(
                'http://127.0.0.1:8008/analyze',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 400:
                result = response.json()
                if result.get("status") == "error" and "validation" in result.get("error_type", ""):
                    print("✅ Empty prompts correctly rejected")
                    return True
                else:
                    print(f"❌ Unexpected error response: {result}")
                    return False
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_invalid_model():
    """Test with invalid model parameter."""
    print("🧪 Testing invalid model...")
    
    # Create a valid video file
    test_file = "test_video.mp4"
    with open(test_file, "wb") as f:
        f.write(b"fake video data")
    
    try:
        with open(test_file, "rb") as f:
            files = {'file': (test_file, f, 'video/mp4')}
            data = {'prompts': 'person, car', 'model': 'invalid_model'}
            
            response = requests.post(
                'http://127.0.0.1:8008/analyze',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 400:
                result = response.json()
                if result.get("status") == "error" and "validation" in result.get("error_type", ""):
                    print("✅ Invalid model correctly rejected")
                    return True
                else:
                    print(f"❌ Unexpected error response: {result}")
                    return False
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_large_file():
    """Test with a file that's too large."""
    print("🧪 Testing large file...")
    
    # Create a large file (>500MB)
    test_file = "test_large.mp4"
    chunk_size = 1024 * 1024  # 1MB chunks
    target_size = 501 * 1024 * 1024  # 501MB
    
    try:
        with open(test_file, "wb") as f:
            written = 0
            while written < target_size:
                chunk = b"0" * min(chunk_size, target_size - written)
                f.write(chunk)
                written += len(chunk)
        
        with open(test_file, "rb") as f:
            files = {'file': (test_file, f, 'video/mp4')}
            data = {'prompts': 'person, car', 'model': 'clip'}
            
            response = requests.post(
                'http://127.0.0.1:8008/analyze',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 400:
                result = response.json()
                if result.get("status") == "error" and "validation" in result.get("error_type", ""):
                    print("✅ Large file correctly rejected")
                    return True
                else:
                    print(f"❌ Unexpected error response: {result}")
                    return False
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def test_health_endpoint():
    """Test health endpoint."""
    print("🧪 Testing health endpoint...")
    
    try:
        response = requests.get('http://127.0.0.1:8008/health', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok":
                print("✅ Health endpoint working")
                return True
            else:
                print(f"❌ Health endpoint returned unexpected status: {result}")
                return False
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health test failed: {e}")
        return False

def test_environment_endpoint():
    """Test environment endpoint."""
    print("🧪 Testing environment endpoint...")
    
    try:
        response = requests.get('http://127.0.0.1:8008/environment', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if "is_colab" in result and "paths" in result:
                print("✅ Environment endpoint working")
                print(f"   Environment: {'Colab' if result['is_colab'] else 'Local'}")
                return True
            else:
                print(f"❌ Environment endpoint returned unexpected data: {result}")
                return False
        else:
            print(f"❌ Environment endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Run all error handling tests."""
    print("🚀 ERROR HANDLING TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_environment_endpoint,
        test_invalid_file_type,
        test_empty_prompts,
        test_invalid_model,
        test_large_file
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL ERROR HANDLING TESTS PASSED!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    main() 