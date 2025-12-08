"""
WebSocket Client Test Script for Live Alerts.

Tests the WebSocket endpoint by connecting and receiving alerts.
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_websocket_connection(uri: str = "ws://127.0.0.1:8000/ws/live", camera_id: str = ""):
    """
    Test WebSocket connection and receive alerts.
    
    Args:
        uri: WebSocket URI
        camera_id: Optional camera ID
    """
    if camera_id:
        uri = f"{uri}?cameraId={camera_id}"
    
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket server")
            
            # Send initial ping
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            logger.info("Sent ping message")
            
            alert_count = 0
            start_time = datetime.now()
            
            # Receive messages
            try:
                while True:
                    # Set timeout for receiving messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    except asyncio.TimeoutError:
                        # Send another ping to keep connection alive
                        await websocket.send(json.dumps({"type": "ping"}))
                        logger.info("Sent ping (timeout)")
                        continue
                    
                    try:
                        data = json.loads(message)
                        
                        if data.get("type") == "pong":
                            logger.info("Received pong (heartbeat)")
                            continue
                        
                        if data.get("type") == "alert":
                            alert = data.get("data", {})
                            alert_count += 1
                            
                            # Verify required fields
                            required_fields = ["stream_id", "timestamp", "frame_index", "category", "confidence"]
                            missing_fields = [f for f in required_fields if f not in alert]
                            
                            if missing_fields:
                                logger.warning(f"⚠️  Alert #{alert_count} missing fields: {missing_fields}")
                            else:
                                logger.info("=" * 60)
                                logger.info(f"🚨 ALERT #{alert_count}")
                                logger.info(f"  Stream ID: {alert.get('stream_id')}")
                                logger.info(f"  Timestamp: {alert.get('timestamp')}")
                                logger.info(f"  Frame Index: {alert.get('frame_index')}")
                                logger.info(f"  Category: {alert.get('category')}")
                                logger.info(f"  Labels: {alert.get('labels', [])}")
                                logger.info(f"  Confidence: {alert.get('confidence'):.3f}")
                                logger.info("=" * 60)
                        else:
                            logger.info(f"Received message: {data}")
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON message: {message}")
                    
                    # Stop after 60 seconds or 10 alerts (whichever comes first)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > 60 or alert_count >= 10:
                        logger.info(f"Test complete: {alert_count} alerts received in {elapsed:.1f}s")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
            except Exception as e:
                logger.error(f"Error receiving messages: {e}", exc_info=True)
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed by server")
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)


async def test_multiple_clients():
    """Test multiple simultaneous WebSocket connections."""
    logger.info("Testing multiple client connections...")
    
    async def client_task(client_id: int):
        uri = f"ws://127.0.0.1:8000/ws/live?cameraId=client_{client_id}"
        try:
            async with websockets.connect(uri) as ws:
                logger.info(f"Client {client_id} connected")
                alert_count = 0
                
                try:
                    while True:
                        message = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "alert":
                            alert_count += 1
                            logger.info(f"Client {client_id} received alert #{alert_count}")
                        
                        if alert_count >= 3:
                            break
                            
                except asyncio.TimeoutError:
                    logger.info(f"Client {client_id} timeout (no alerts)")
        except Exception as e:
            logger.error(f"Client {client_id} error: {e}")
    
    # Connect 3 clients simultaneously
    tasks = [client_task(i) for i in range(1, 4)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("Multiple client test complete")


async def main():
    """Main test function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        await test_multiple_clients()
    else:
        await test_websocket_connection()


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Client Test")
    print("=" * 60)
    print("Make sure the backend is running with live.enabled=true")
    print("=" * 60)
    print()
    
    asyncio.run(main())

