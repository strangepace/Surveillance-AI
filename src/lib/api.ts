// Centralized API helpers with robust request wrapper
// Reads base URL from env (API_BASE_URL preferred) with relative fallback in dev

export type JobStatus = {
  status: string; // e.g., queued | processing | complete | error
  progress?: number; // 0..100
  etaSeconds?: number | null;
  message?: string;
};

export type ResultEntry = {
  timestamp: string;
  labels: string[];
  confidence: number; // 0..1
  preview_clip: string;
};

export type AnalysisResponse = {
  status: string;
  video_id: string;
  results: ResultEntry[];
  alert_summary?: Record<string, number>;
  analysis_timestamp?: string;
  json_path?: string;
};

export type ExportStart = { exportId: string };
export type ExportStatus = { status: string; url?: string; sizeBytes?: number };

export type HealthInfo = {
  device?: string;
  gpu?: string;
  modelCache?: string;
  [key: string]: any;
};

export type ApiError = {
  status: number;
  code: string;
  message: string;
  details?: any;
};

// Resolve HTTP and WS bases from multiple env conventions
// Support: Vite (VITE_*), generic (API_BASE_URL/WS_BASE_URL), Next-style (NEXT_PUBLIC_*)
export const API_BASE: string =
  (import.meta as any)?.env?.VITE_API_BASE_URL ||
  (import.meta as any)?.env?.API_BASE_URL ||
  (import.meta as any)?.env?.NEXT_PUBLIC_API_BASE_URL ||
  "";

export const WS_BASE: string =
  (import.meta as any)?.env?.VITE_WS_BASE_URL ||
  (import.meta as any)?.env?.WS_BASE_URL ||
  (import.meta as any)?.env?.NEXT_PUBLIC_WS_BASE_URL ||
  (() => {
    try {
      if (!API_BASE) return ""; // derive relative later
      const u = new URL(API_BASE, window.location.href);
      const wsProto = u.protocol === "https:" ? "wss:" : "ws:";
      return `${wsProto}//${u.host}`;
    } catch {
      return "";
    }
  })();

// Optional auth header hook (no-op by default)
function getAuthHeaders(): Record<string, string> {
  // TODO: inject Authorization header if needed
  return {};
}

async function parseJsonSafe(res: Response): Promise<any> {
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    try {
      return await res.json();
    } catch (e) {
      throw <ApiError>{ status: res.status, code: "BAD_JSON", message: "Invalid JSON response", details: e };
    }
  }
  try {
    const text = await res.text();
    // try parse JSON from text if looks like JSON
    if (text && (text.startsWith("{") || text.startsWith("["))) {
      try { return JSON.parse(text); } catch {}
    }
    return { message: text };
  } catch (e) {
    throw <ApiError>{ status: res.status, code: "READ_ERROR", message: "Failed to read response", details: e };
  }
}

export async function request<T>(path: string, init: (RequestInit & { timeoutMs?: number }) = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = init.timeoutMs ?? 20000;
  const t = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const base = API_BASE || ""; // relative allowed
    const url = `${base}${path}`;
    const headers = {
      "Accept": "application/json",
      ...(init.headers || {}),
      ...getAuthHeaders(),
    } as Record<string, string>;
    const res = await fetch(url, { ...init, headers, signal: controller.signal });
    const body = await parseJsonSafe(res);
    if (!res.ok) {
      const message = body?.message || `HTTP ${res.status}`;
      const code = (body?.code as string) || (res.status >= 500 ? "SERVER_ERROR" : "CLIENT_ERROR");
      throw <ApiError>{ status: res.status, code, message, details: body };
    }
    return body as T;
  } catch (e: any) {
    if (e?.name === "AbortError") {
      throw <ApiError>{ status: 0, code: "TIMEOUT", message: `Request timed out after ${timeoutMs}ms` };
    }
    if (e && typeof e.status === "number" && e.code) throw e as ApiError;
    // Network-level failure
    throw <ApiError>{ status: 0, code: "NETWORK_ERROR", message: e?.message || "Network error", details: e };
  } finally {
    clearTimeout(t);
  }
}

export const api = {
  getStatus: (jobId: string) => request<JobStatus>(`/status?jobId=${encodeURIComponent(jobId)}`),
  getResults: (jobId: string) => request<AnalysisResponse>(`/results?jobId=${encodeURIComponent(jobId)}`),
  postExportClips: (jobId: string) => request<ExportStart>(`/export-clips`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jobId }),
  }),
  getExportStatus: (exportId: string) => request<ExportStatus>(`/export-status?exportId=${encodeURIComponent(exportId)}`),
  getHealth: () => request<HealthInfo>(`/health`),

  // Live REST endpoints (Phase-1)
  getLiveAlerts: (cameraId: string, since?: number, limit = 200) =>
    request<any>(`/live/alerts?cameraId=${encodeURIComponent(cameraId)}${since ? `&since=${since}` : ""}&limit=${limit}`),
  postLiveAck: (alertId: string, acknowledged: boolean) =>
    request<{ ok: boolean }>(`/live/acknowledge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alertId, acknowledged }),
    }),
  postLivePin: (alertId: string, pinned: boolean) =>
    request<{ ok: boolean }>(`/live/pin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alertId, pinned }),
    }),
  postLiveNote: (alertId: string, note: string) =>
    request<{ ok: boolean }>(`/live/note`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alertId, note }),
    }),
  postLiveExport: (alertId: string) =>
    request<{ exportId: string }>(`/live/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alertId }),
    }),
  getLiveExportStatus: (exportId: string) =>
    request<{ status: string; url?: string; sizeBytes?: number }>(`/live/export/status?exportId=${encodeURIComponent(exportId)}`),

  // Utility exposure for non-listed endpoints
  apiFetch: request,
};

export default api;
