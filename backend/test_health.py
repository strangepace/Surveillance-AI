#!/usr/bin/env python3
"""
Health check test for backend.
"""
import requests

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get('http://127.0.0.1:8008/health', timeout=10)
        if response.status_code == 200:
            print(f"✅ Health check: {response.status_code}")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    test_health() 
