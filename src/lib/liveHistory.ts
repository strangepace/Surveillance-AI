import { api } from "./api";
import type { Alert } from "@/context/live-types";

export type FetchLiveHistoryParams = {
  cameraId: string;
  since?: number;
  limit?: number;
  signal?: AbortSignal;
};

export async function fetchLiveHistory({ cameraId, since, limit = 200, signal }: FetchLiveHistoryParams): Promise<Alert[]> {
  const qs = new URLSearchParams();
  qs.set("cameraId", cameraId);
  if (since) qs.set("since", String(since));
  if (limit) qs.set("limit", String(limit));
  const res = await api.apiFetch<Alert[]>(`/live/alerts?${qs.toString()}`, { signal });
  return Array.isArray(res) ? res : [];
}
