#!/usr/bin/env python3
"""
Test script for Live Alert API endpoints
"""
import asyncio
import websockets
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def test_live_endpoints():
    """Test all live REST endpoints"""
    print("🧪 Testing Live Alert REST API...")
    
    # 1. Generate a demo alert
    print("\n1. Generating demo alert...")
    response = requests.post(f"{BASE_URL}/live/demo/generate", 
                           params={"cameraId": "CAM123"})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Demo alert generated: {result['message']}")
    
    # 2. Get alert history
    print("\n2. Fetching alert history...")
    response = requests.get(f"{BASE_URL}/live/alerts", 
                          params={"cameraId": "CAM123", "limit": 10})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        alerts_data = response.json()
        print(f"✅ Found {len(alerts_data['alerts'])} alerts")
        
        if alerts_data['alerts']:
            alert = alerts_data['alerts'][0]
            alert_id = alert['alertId']
            print(f"Latest alert: {alert_id} - {alert['labels']}")
            
            # 3. Test alert actions
            print(f"\n3. Testing alert actions on {alert_id}...")
            
            # Acknowledge alert
            ack_response = requests.post(f"{BASE_URL}/live/acknowledge",
                                       json={"alertId": alert_id, "acknowledged": True})
            print(f"Acknowledge: {ack_response.status_code} - {ack_response.json()['message']}")
            
            # Pin alert
            pin_response = requests.post(f"{BASE_URL}/live/pin",
                                       json={"alertId": alert_id, "pinned": True})
            print(f"Pin: {pin_response.status_code} - {pin_response.json()['message']}")
            
            # Add note
            note_response = requests.post(f"{BASE_URL}/live/note",
                                        json={"alertId": alert_id, "note": "Test note from API"})
            print(f"Note: {note_response.status_code} - {note_response.json()['message']}")
            
            # Export alert
            export_response = requests.post(f"{BASE_URL}/live/export",
                                          json={"alertId": alert_id})
            if export_response.status_code == 200:
                export_data = export_response.json()
                export_id = export_data['exportId']
                print(f"Export started: {export_id}")
                
                # Check export status
                status_response = requests.get(f"{BASE_URL}/live/export/status",
                                             params={"exportId": export_id})
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Export status: {status_data}")

async def test_websocket():
    """Test WebSocket live streaming"""
    print("\n🌐 Testing WebSocket connection...")
    
    try:
        uri = f"{WS_URL}/ws/live?cameraId=CAM123"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"Welcome: {welcome_data}")
            
            # Generate a demo alert to test real-time streaming
            print("Generating demo alert to test streaming...")
            requests.post(f"{BASE_URL}/live/demo/generate", 
                         params={"cameraId": "CAM123"})
            
            # Listen for the alert
            try:
                alert_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                alert_data = json.loads(alert_message)
                if alert_data.get('type') == 'alert':
                    print(f"✅ Received live alert: {alert_data['data']['alertId']}")
                    print(f"   Labels: {alert_data['data']['labels']}")
                    print(f"   Category: {alert_data['data']['category']}")
                else:
                    print(f"Received: {alert_data}")
            except asyncio.TimeoutError:
                print("⚠️  No alert received within timeout")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

def test_alert_filtering():
    """Test alert filtering and pagination"""
    print("\n📋 Testing alert filtering...")
    
    # Generate multiple alerts for different cameras
    cameras = ["CAM123", "CAM456", "CAM789"]
    for camera in cameras:
        for _ in range(3):
            requests.post(f"{BASE_URL}/live/demo/generate", 
                         params={"cameraId": camera})
            time.sleep(0.1)  # Small delay
    
    # Test camera filtering
    for camera in cameras:
        response = requests.get(f"{BASE_URL}/live/alerts",
                              params={"cameraId": camera, "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"Camera {camera}: {len(data['alerts'])} alerts")
            
            # Verify all alerts are from correct camera
            for alert in data['alerts']:
                assert alert['cameraId'] == camera, f"Wrong camera: {alert['cameraId']}"
    
    # Test pagination
    response = requests.get(f"{BASE_URL}/live/alerts",
                          params={"limit": 5, "page": 1})
    if response.status_code == 200:
        data = response.json()
        print(f"Pagination test: Page 1 has {len(data['alerts'])} alerts, total: {data['total']}")

def main():
    """Run all tests"""
    print("🚀 Starting Live Alert API Tests...")
    
    try:
        # Test REST endpoints
        test_live_endpoints()
        
        # Test filtering
        test_alert_filtering()
        
        # Test WebSocket (async)
        asyncio.run(test_websocket())
        
        print("\n✅ All Live API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python -m uvicorn app:app --reload")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
