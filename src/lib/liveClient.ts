// Lightweight WebSocket client for live alerts with reconnect/heartbeat
import { API_BASE, WS_BASE } from "./api";

export type LiveWsMessage =
  | { type: "pong" }
  | { type: "alert"; data: any }
  | { type: string; [k: string]: any };

export type LiveClientOptions = {
  cameraId: string;
  onAlert: (alert: any) => void;
  onStatus?: (s: "connecting" | "connected" | "disconnected" | "unstable" | "error", reason?: string) => void;
  forceMock?: boolean;
};

function toWsUrl(path: string) {
  // Prefer explicit WS_BASE; otherwise derive from API_BASE; finally fall back to window location
  const cleanJoin = (baseHost: string, p: string) => `${baseHost}${p.startsWith("/") ? p : `/${p}`}`;
  try {
    if (WS_BASE) {
      // WS_BASE is full origin like wss://host:port
      return cleanJoin(WS_BASE, path);
    }
    if (API_BASE) {
      const u = new URL(API_BASE, window.location.href);
      const wsProto = u.protocol === "https:" ? "wss:" : "ws:";
      const host = `${wsProto}//${u.host}`;
      return cleanJoin(host, path);
    }
    const loc = window.location;
    const proto = loc.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${loc.host}${path}`;
  } catch {
    const loc = window.location;
    const proto = loc.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${loc.host}${path}`;
  }
}

export class LiveClient {
  private ws: WebSocket | null = null;
  private opts!: LiveClientOptions;
  private hbTimer: number | undefined;
  private idleTimer: number | undefined;
  private reconnects = 0;
  private lastMessageTs = 0;
  private closedByUser = false;

  connect(opts: LiveClientOptions) {
    this.opts = opts;
    this.closedByUser = false;
    this.open();
  }

  private open() {
    if (this.opts.forceMock) {
      this.opts.onStatus?.("error", "forced-mock");
      return;
    }
    this.opts.onStatus?.("connecting");
    const url = toWsUrl(`/ws/live?cameraId=${encodeURIComponent(this.opts.cameraId || "")}`);
    try {
      this.ws = new WebSocket(url);
    } catch (e: any) {
      this.opts.onStatus?.("error", e?.message || "constructor");
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnects = 0;
      this.lastMessageTs = Date.now();
      this.opts.onStatus?.("connected");
      this.startHeartbeat();
      this.startIdleWatch();
    };

    this.ws.onmessage = (ev) => {
      this.lastMessageTs = Date.now();
      try {
        const msg: LiveWsMessage = JSON.parse(ev.data);
        if (msg.type === "pong") return;
        if (msg.type === "alert" && (msg as any).data) {
          this.opts.onAlert((msg as any).data);
        }
      } catch {
        // ignore
      }
    };

    this.ws.onclose = (ev) => {
      this.cleanupTimers();
      this.opts.onStatus?.("disconnected", `code:${ev.code}`);
      if (!this.closedByUser) this.scheduleReconnect();
    };

    this.ws.onerror = (ev: Event) => {
      this.opts.onStatus?.("error", (ev as any)?.message || "socket");
    };
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    const sendPing = () => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      try { this.ws.send(JSON.stringify({ type: "ping" })); } catch {}
      this.hbTimer = window.setTimeout(sendPing, 25000);
    };
    this.hbTimer = window.setTimeout(sendPing, 25000);
  }

  private stopHeartbeat() {
    if (this.hbTimer) { clearTimeout(this.hbTimer); this.hbTimer = undefined; }
  }

  private startIdleWatch() {
    if (this.idleTimer) clearInterval(this.idleTimer);
    this.idleTimer = window.setInterval(() => {
      if (Date.now() - this.lastMessageTs > 40000) {
        this.opts.onStatus?.("unstable", "heartbeat");
        this.forceReconnect();
      }
    }, 5000) as any;
  }

  private cleanupTimers() {
    this.stopHeartbeat();
    if (this.idleTimer) { clearInterval(this.idleTimer); this.idleTimer = undefined; }
  }

  private scheduleReconnect() {
    this.reconnects += 1;
    const base = Math.min(30000, 1000 * Math.pow(2, this.reconnects - 1));
    const jitter = base * 0.15;
    const delay = base + (Math.random() * 2 - 1) * jitter;
    window.setTimeout(() => this.open(), delay);
  }

  private forceReconnect() {
    try { this.ws?.close(); } catch {}
  }

  disconnect() {
    this.closedByUser = true;
    this.cleanupTimers();
    try { this.ws?.close(); } catch {}
    this.ws = null;
  }
}
