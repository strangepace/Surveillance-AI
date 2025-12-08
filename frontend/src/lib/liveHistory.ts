import { api } from "./api";
import type { Alert } from "@/context/live-types";

export type FetchLiveHistoryParams = {
  cameraId: string;
  windowSec?: number;
  limit?: number;
  signal?: AbortSignal;
};

export async function fetchLiveHistory({ cameraId, windowSec = 600, limit = 200, signal }: FetchLiveHistoryParams): Promise<Alert[]> {
  const qs = new URLSearchParams();
  if (cameraId) qs.set("streamId", cameraId);
  if (windowSec) qs.set("windowSec", String(windowSec));
  if (limit) qs.set("limit", String(limit));
  const res = await api.apiFetch<{ alerts: Alert[] }>(`/live/alerts/recent?${qs.toString()}`, { signal });
  return Array.isArray((res as any)?.alerts) ? (res as any).alerts : Array.isArray(res as any) ? (res as any) : [];
}
