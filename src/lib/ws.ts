// WebSocket helpers and re-exports for external usage
// This keeps naming consistent for consumers expecting `lib/ws`.

import { API_BASE, WS_BASE } from "./api";
export { LiveClient } from "./liveClient";
export type { LiveWsMessage, LiveClientOptions } from "./liveClient";

// Build a websocket URL using the same precedence as LiveClient:
// 1) Explicit WS_BASE (origin only)
// 2) Derive from API_BASE (http->ws, https->wss)
// 3) Fallback to window.location
export function toWsUrl(path: string): string {
  const cleanJoin = (baseHost: string, p: string) => `${baseHost}${p.startsWith("/") ? p : `/${p}`}`;
  try {
    if (WS_BASE) {
      return cleanJoin(WS_BASE, path);
    }
    if (API_BASE) {
      const u = new URL(API_BASE, typeof window !== "undefined" ? window.location.href : "http://localhost");
      const wsProto = u.protocol === "https:" ? "wss:" : "ws:";
      const host = `${wsProto}//${u.host}`;
      return cleanJoin(host, path);
    }
    if (typeof window !== "undefined") {
      const loc = window.location;
      const proto = loc.protocol === "https:" ? "wss:" : "ws:";
      return `${proto}//${loc.host}${path}`;
    }
  } catch {
    // fall through to final fallback
  }
  if (typeof window !== "undefined") {
    const loc = window.location;
    const proto = loc.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${loc.host}${path}`;
  }
  return path; // non-browser last resort
}
