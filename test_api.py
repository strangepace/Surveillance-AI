#!/usr/bin/env python3
"""
Simple test script for the Surveillance AI API endpoints.
"""

import requests
import json
import os
from pathlib import Path

def test_manual_upload():
    """Test the manual upload endpoint."""
    
    # Check if video file exists
    video_path = "content/uploads/tupaki_footage.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"✅ Found video file: {video_path}")
    
    # Prepare the request
    url = "http://localhost:8000/api/v1/analyze-manual"
    
    files = {
        'video': ('tupaki_footage.mp4', open(video_path, 'rb'), 'video/mp4')
    }
    
    data = {
        'prompt': 'find any suspicious activity or weapons',
        'model': 'chatgpt'
    }
    
    print("🚀 Testing manual upload endpoint...")
    print(f"URL: {url}")
    print(f"Prompt: {data['prompt']}")
    print(f"Model: {data['model']}")
    print("⏳ Processing... (this may take 30-60 seconds)")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=600)  # 10 minutes timeout
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Status: {result.get('status')}")
            print(f"Analysis Type: {result.get('analysis_type')}")
            
            # Check for alerts
            alerts = result.get('alerts', {})
            if alerts.get('alert'):
                print(f"🚨 ALERT DETECTED: {alerts.get('alert_level', 'unknown').upper()}")
                print(f"Total Alert Events: {alerts.get('total_alert_events', 0)}")
                for event in alerts.get('alert_events', []):
                    print(f"  - {event.get('category')}: {event.get('event')} (confidence: {event.get('confidence', 0):.2f})")
            else:
                print("✅ No alerts detected")
            
            # Show processing time
            processing = result.get('processing', {})
            print(f"⏱️ Total Time: {processing.get('total_time_seconds', 0):.2f}s")
            print(f"📹 Video Processing: {processing.get('video_processing_time', 0):.2f}s")
            print(f"🤖 LLM Processing: {processing.get('llm_processing_time', 0):.2f}s")
            
            # Show AI answer
            ai_answer = result.get('analysis', {}).get('ai_answer', 'No answer provided')
            print(f"\n🤖 AI Answer:\n{ai_answer}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (video processing took too long)")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_health_endpoint():
    """Test the health endpoint."""
    
    url = "http://localhost:8000/api/v1/health/detailed"
    
    print("🏥 Testing health endpoint...")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check passed!")
            print(f"Status: {result.get('status')}")
            
            # Show API key status
            api_keys = result.get('api_keys', {})
            print(f"OpenAI: {'✅' if api_keys.get('openai_available') else '❌'}")
            print(f"Gemini: {'✅' if api_keys.get('gemini_available') else '❌'}")
            print(f"Google Credentials: {'✅' if api_keys.get('google_credentials_available') else '❌'}")
            
            # Show system info
            system = result.get('system', {})
            print(f"CPU: {system.get('cpu_percent', 0):.1f}%")
            print(f"Memory: {system.get('memory_percent', 0):.1f}%")
            print(f"Disk: {system.get('disk_percent', 0):.1f}%")
            
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

def main():
    """Main test function."""
    
    print("🧪 Surveillance AI API Test")
    print("=" * 50)
    
    # Test health endpoint first
    test_health_endpoint()
    print()
    
    # Test manual upload
    test_manual_upload()
    print()
    
    print("🏁 Test completed!")

if __name__ == "__main__":
    main() 