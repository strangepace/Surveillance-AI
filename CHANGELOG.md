# Changelog

All notable changes to this project will be documented in this file.

## Phase‑1 Complete (planned v0.1.0) – 2025‑08‑10

Highlights
- Live WebSocket client (src/lib/liveClient.ts) with heartbeat, idle watch, and exponential backoff reconnect
- Automatic fallback to mock mode after repeated instability/failures
- DevBanner component to surface connection state (mock/unstable/developer setting)
- Optimistic updates for live actions: acknowledge, pin, note
- Export clip flow in LiveReview with progress and open‑export link
- Live Alerts page with URL‑synced filters and virtualized list for performance
- Minor fixes and accessibility/semantic improvements in headers and buttons

Details
- Context and state: LiveProvider exposes live.connect/disconnect/history and REST actions (ack/pin/note/export)
- Persistence: recent alerts saved to localStorage with requestIdleCallback when available
- Filtering/Sorting: category, search, confidence range, time range, cameraId; sort by newest/oldest/confidence
- Mocking: Dev Panel to simulate categories, jitter FPS, and trigger bursts; developer can toggle real API usage

Upgrade notes
- No breaking API changes to consumers of components; feature flags and developer settings are persisted locally
- package.json version bump is documented here as "planned v0.1.0" due to repository constraints

