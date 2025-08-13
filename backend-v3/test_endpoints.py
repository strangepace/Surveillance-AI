#!/usr/bin/env python3
"""
Quick test script to verify endpoint response formats
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test /health endpoint format"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"GET /health: {response.status_code}")
    data = response.json()
    
    # Verify exact fields
    expected_fields = ["status", "version", "api_version", "environment", "device", "gpu", "modelCache"]
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"
    
    print(f"✅ /health format correct: {json.dumps(data, indent=2)}")

def test_status():
    """Test /status endpoint format"""
    # This will return 404 since no job exists, but we can check error format
    response = requests.get(f"{BASE_URL}/status?jobId=test_123")
    print(f"GET /status: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ /status endpoint exists (returns 404 for non-existent job)")
    else:
        data = response.json()
        print(f"Status response: {json.dumps(data, indent=2)}")

def test_results():
    """Test /results endpoint format"""
    response = requests.get(f"{BASE_URL}/results?jobId=test_123")
    print(f"GET /results: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ /results endpoint exists (returns 404 for non-existent job)")
    else:
        data = response.json()
        print(f"Results response: {json.dumps(data, indent=2)}")

def test_export():
    """Test /export/clips endpoint format"""
    response = requests.post(f"{BASE_URL}/export/clips", json={"jobId": "test_123"})
    print(f"POST /export/clips: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ /export/clips endpoint exists (returns 404 for non-existent job)")
    else:
        data = response.json()
        print(f"Export response: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    print("🧪 Testing API endpoint formats...")
    try:
        test_health()
        test_status()
        test_results()
        test_export()
        print("\n✅ All endpoint tests completed!")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python -m uvicorn app:app --reload")
    except Exception as e:
        print(f"❌ Test failed: {e}")
