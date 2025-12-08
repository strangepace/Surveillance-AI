# Live Analytics Backend

## Live-Stream Processing Pipeline (MVP)
- **What it does**: Ingests frames from a single source (file/RTSP/camera), samples at target FPS, runs CLIP-based detection, emits alerts.
- **Key components**: `live_source.py`, `live_detector.py`, `live_pipeline.py`.
- **Config**: `config/clip_config.yaml` → `live.enabled`, `live.source_type`, `live.source_path`, `live.sample_fps`, `live.prompts`, queue sizes, buffer window.
- **Flow**: LiveSource → frame queue → LiveDetector → alerts queue → (buffer/WebSocket).
- **Testing**: Set `live.enabled=true`, source to a local mp4, start backend, observe `🚨 LIVE ALERT` logs.

## WebSocket Server for Live Alerts
- **Endpoint**: `GET /ws/live?cameraId=<id>` (FastAPI WebSocket).
- **Payloads**:
  - Client → Server: `{ "type": "ping" }`
  - Server → Client: `{ "type": "pong" }`
  - Alerts: `{ "type": "alert", "data": { ...alert fields... } }`
- **Behavior**: Broadcasts every alert to all connected clients; supports heartbeat; cleans up disconnects.
- **Key code**: `app.py` (websocket handlers, broadcaster).
- **Testing**: Use browser DevTools or `backend/test_websocket_client.py`; verify alerts stream and pong replies.

## Live Storage Buffer & Replay
- **What it does**: In-memory buffer of recent alerts per stream for refresh/scrubbing.
- **Retention**: `live.buffer_window_sec` (default 600s) in `config/clip_config.yaml`.
- **Key components**: `live_buffer.py`; integration in `app.py` (startup init, buffer cleanup, broadcaster writes to buffer).
- **Endpoints**:
  - `GET /live/alerts/recent?streamId=default&windowSec=600` → alerts in ascending order (oldest→newest).
  - `GET /live/buffer/stats` → retention, counts, per-stream totals.
  - `GET /live/buffer/streams` → active stream IDs.
- **Behavior**: Every live alert is stored + broadcast; old alerts evicted on insert and via periodic cleanup; empty list if none yet.
- **Testing**: Run live pipeline, generate alerts, call `/live/alerts/recent`; verify within window and that old alerts fall off over time.

