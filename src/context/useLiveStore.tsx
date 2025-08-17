import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import flags from "@/lib/config";
import { api, API_BASE } from "@/lib/api";
import { LiveClient } from "@/lib/liveClient";
import { Alert, Category, ConnectionStatus, DevOptions, LiveFilters, LiveStoreState } from "./live-types";
import { filterAlerts, sortAlerts } from "./live-selectors";
import { loadAlerts, saveAlertsIdle, loadDev as loadDevPersist, saveDev as saveDevPersist } from "./live-persist";
import { useToast } from "@/components/ui/use-toast";

const DEFAULT_DEV: DevOptions = {
  simCategories: { people: true, color: true, fire: true, vehicle: true, weapon: false, activity: true },
  jitterFps: false,
  useRealApi: true,
};

function genId() { return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`; }

// Mock helpers
const cameras = ["cam-1", "cam-2", "cam-3", "lobby", "dock"];
const tagPool: Record<Category, string[]> = {
  people: ["person", "people", "adult", "child"],
  color: ["red", "blue", "black", "green", "yellow"],
  fire: ["fire", "smoke", "flame"],
  vehicle: ["vehicle", "car", "truck", "suv"],
  weapon: ["knife", "gun", "rifle"],
  activity: ["running", "fall", "trespass", "loiter"],
};
function randInt(n: number) { return Math.floor(Math.random() * n); }
function sample<T>(arr: T[]): T { return arr[randInt(arr.length)]; }
function genMockAlert(enabledCats: Category[]): Alert {
  const ts = Math.floor(Date.now() / 1000);
  const category = sample(enabledCats);
  const labels = Array.from(new Set([...Array.from({ length: 1 + randInt(3) }, () => sample(tagPool[category]))]));
  const id = genId();
  return {
    alertId: id,
    cameraId: sample(cameras),
    tsUnix: ts,
    timestamp: new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    labels,
    category,
    confidence: Math.round((0.55 + Math.random() * 0.45) * 100) / 100,
    thumbnailUrl: "/placeholder.svg",
    clipUrl: "",
    pinned: false,
    acknowledged: false,
    _animate: true,
  };
}

const LiveStoreCtx = createContext<LiveStoreState | null>(null);

export const LiveProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { toast } = useToast();
  const [alerts, setAlerts] = useState<Alert[]>(() => loadAlerts());
  const [filters, setFiltersState] = useState<LiveFilters>(() => ({
    categories: new Set(),
    search: "",
    sort: "newest",
    confidenceRange: [0, 1],
    timeRange: "24h",
    cameraId: null,
  }));
  const persistedDev = loadDevPersist();
  const [dev, setDev] = useState<DevOptions>(() => ({
    ...DEFAULT_DEV,
    simCategories: { ...DEFAULT_DEV.simCategories, ...(persistedDev?.simCategories ?? {}) },
    jitterFps: persistedDev?.jitterFps ?? DEFAULT_DEV.jitterFps,
    useRealApi: persistedDev?.useRealApi ?? DEFAULT_DEV.useRealApi,
  }));
  const [connection, setConnection] = useState<ConnectionStatus>("idle");

  // Save effects
  useEffect(() => saveAlertsIdle(alerts), [alerts]);
  useEffect(() => saveDevPersist({ simCategories: dev.simCategories, jitterFps: dev.jitterFps, useRealApi: dev.useRealApi }), [dev]);

  // WS client
  const wsRef = useRef<LiveClient | null>(null);
  const activeCameraRef = useRef<string | null>(null);
  // Track repeated failures to auto-fallback to mock
  const failCountRef = useRef(0);
  const firstFailAtRef = useRef<number>(0);

  const addAlerts = (list: Alert[]) => {
    setAlerts((prev) => {
      const map = new Map(prev.map((a) => [a.alertId, a] as const));
      for (const a of list) map.set(a.alertId, a);
      return sortAlerts(Array.from(map.values()), "newest").slice(0, 500);
    });
  };

  const applyOptimistic = (id: string, patch: Partial<Alert>) => {
    setAlerts((prev) => prev.map((a) => (a.alertId === id ? { ...a, ...patch } : a)));
  };

  const noteCtrlsRef = useRef<Map<string, AbortController>>(new Map());
  // Mock generator (enabled when: flags.enableLiveMock AND (dev.useRealApi=false OR API unavailable))
  const mockTimer = useRef<number | undefined>(undefined);
  const mockFlushTimer = useRef<number | undefined>(undefined);
  const mockBuf = useRef<Alert[]>([]);
  const mockRunning = useRef(false);
  const startMock = () => {
    if (!flags.enableLiveMock || mockRunning.current) return;
    mockRunning.current = true;
    setConnection("mock");
    const enabledCats = (Object.keys(dev.simCategories) as Category[]).filter((c) => dev.simCategories[c]);
    const flush = () => {
      if (!mockBuf.current.length) return;
      addAlerts(mockBuf.current);
      mockBuf.current = [];
    };
    const scheduleFlush = () => {
      if (mockFlushTimer.current) return;
      mockFlushTimer.current = window.setTimeout(() => {
        mockFlushTimer.current = undefined;
        flush();
      }, 200);
    };
    const loop = () => {
      const ms = 4000 + Math.floor(Math.random() * 5000);
      mockTimer.current = window.setTimeout(() => {
        const count = 1 + randInt(2);
        for (let i = 0; i < count; i++) mockBuf.current.push(genMockAlert(enabledCats));
        scheduleFlush();
        loop();
      }, ms);
    };
    loop();
  };
  const stopMock = () => {
    mockRunning.current = false;
    if (mockTimer.current) clearTimeout(mockTimer.current);
    if (mockFlushTimer.current) clearTimeout(mockFlushTimer.current);
  };

  // Live connect/disconnect
  const liveConnect = (cameraId?: string | null) => {
    const cam = cameraId ?? filters.cameraId ?? null;
    activeCameraRef.current = cam;
    // Decide whether to use real API
    const forceMock = flags.enableLiveMock || !dev.useRealApi || !API_BASE;
    if (forceMock) {
      stopWs();
      startMock();
      return;
    }
    stopMock();
    if (!wsRef.current) wsRef.current = new LiveClient();
    wsRef.current.connect({
      cameraId: cam || "",
      onAlert: (data: any) => {
        // Assume server alert is compatible or map minimally
        const a: Alert = {
          alertId: data.alertId || data.id,
          cameraId: data.cameraId || cam || data.camera || "",
          tsUnix: data.tsUnix || Math.floor(Date.now() / 1000),
          timestamp: data.timestamp || new Date((data.tsUnix || Math.floor(Date.now() / 1000)) * 1000).toLocaleTimeString(),
          labels: data.labels || [],
          category: data.category || "activity",
          confidence: typeof data.confidence === "number" ? data.confidence : 0.9,
          thumbnailUrl: data.thumbnailUrl || "/placeholder.svg",
          clipUrl: data.clipUrl || "",
          pinned: !!data.pinned,
          acknowledged: !!data.acknowledged,
          note: data.note,
          _animate: true,
        };
        addAlerts([a]);
      },
      onStatus: (s) => {
        setConnection(s);
        if (s === "connected") {
          failCountRef.current = 0;
          firstFailAtRef.current = 0;
        } else if (s === "error" || s === "disconnected" || s === "unstable") {
          const now = Date.now();
          if (!firstFailAtRef.current || now - firstFailAtRef.current > 60000) {
            firstFailAtRef.current = now;
            failCountRef.current = 0;
          }
          failCountRef.current += 1;
          if (flags.enableLiveMock && failCountRef.current >= 3) {
            stopWs();
            startMock();
            setConnection("mock");
            failCountRef.current = 0;
            firstFailAtRef.current = 0;
            toast({ title: "Live unstable — using mock data", description: "Fell back after repeated connection issues.", duration: 4000 });
          }
        }
      },
      forceMock: false,
    });
  };

  const stopWs = () => {
    try { wsRef.current?.disconnect(); } catch {}
    wsRef.current = null;
  };

  const liveDisconnect = () => {
    stopWs();
    stopMock();
    setConnection("disconnected");
  };

  // REST actions with optimistic updates
  const announce = (message: string) => {
    try { window.dispatchEvent(new CustomEvent("live-announce", { detail: message })); } catch {}
  };
  const restAck = async (alertId: string, acknowledged: boolean) => {
    const prev = alerts.find((a) => a.alertId === alertId)?.acknowledged ?? false;
    applyOptimistic(alertId, { acknowledged });
    try {
      await api.postLiveAck(alertId, acknowledged);
      toast({ title: acknowledged ? "Acknowledged" : "Unacknowledged", description: `Alert ${alertId}` });
      announce(acknowledged ? "Acknowledged" : "Unacknowledged");
    } catch (e: any) {
      applyOptimistic(alertId, { acknowledged: prev });
      toast({ title: "Acknowledge failed", description: e?.message || String(e), variant: "destructive" });
      announce("Acknowledge failed");
    }
  };
  const restPin = async (alertId: string, pinned: boolean) => {
    const prev = alerts.find((a) => a.alertId === alertId)?.pinned ?? false;
    applyOptimistic(alertId, { pinned });
    try {
      await api.postLivePin(alertId, pinned);
      toast({ title: pinned ? "Pinned" : "Unpinned", description: `Alert ${alertId}` });
      announce(pinned ? "Pinned" : "Unpinned");
    } catch (e: any) {
      applyOptimistic(alertId, { pinned: prev });
      toast({ title: "Pin failed", description: e?.message || String(e), variant: "destructive" });
      announce("Pin failed");
    }
  };
  const restNote = async (alertId: string, note: string) => {
    const prev = alerts.find((a) => a.alertId === alertId)?.note ?? "";
    // Cancel previous save for this alert
    try { noteCtrlsRef.current.get(alertId)?.abort(); } catch {}
    const ctrl = new AbortController();
    noteCtrlsRef.current.set(alertId, ctrl);
    applyOptimistic(alertId, { note });
    try {
      await api.apiFetch(`/live/note`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alertId, note }),
        signal: ctrl.signal,
      } as any);
      toast({ title: "Note saved", description: `Alert ${alertId}` });
      announce("Note saved");
    } catch (e: any) {
      if (e?.name === "AbortError") return; // last write wins
      applyOptimistic(alertId, { note: prev });
      toast({ title: "Save note failed", description: e?.message || String(e), variant: "destructive" });
      announce("Save note failed");
    }
  };

  const fetchHistory = async (params?: { cameraId?: string; since?: number; limit?: number }) => {
    try {
      const cam = params?.cameraId ?? filters.cameraId ?? "";
      const resp = await api.getLiveAlerts(cam, params?.since, params?.limit ?? 200);
      const list: Alert[] = (resp?.alerts || resp || []).map((data: any) => ({
        alertId: data.alertId || data.id,
        cameraId: data.cameraId || cam,
        tsUnix: data.tsUnix || Math.floor(Date.now() / 1000),
        timestamp: data.timestamp || new Date((data.tsUnix || Math.floor(Date.now() / 1000)) * 1000).toLocaleTimeString(),
        labels: data.labels || [],
        category: data.category || "activity",
        confidence: typeof data.confidence === "number" ? data.confidence : 0.9,
        thumbnailUrl: data.thumbnailUrl || "/placeholder.svg",
        clipUrl: data.clipUrl || "",
        pinned: !!data.pinned,
        acknowledged: !!data.acknowledged,
        note: data.note,
      }));
      addAlerts(list);
    } catch (e) {
      setConnection("error");
      if (flags.enableLiveMock) {
        startMock();
        toast({ title: "Live API unavailable — using mock data", description: "Falling back automatically.", duration: 4000 });
      }
    }
  };

  const doExport = async (alertId: string) => {
    const { exportId } = await api.postLiveExport(alertId);
    return exportId;
  };
  const pollExport = async (exportId: string): Promise<{ url?: string; sizeBytes?: number }> => {
    for (;;) {
      const s = await api.getLiveExportStatus(exportId);
      if (s.status === "complete" && s.url) return { url: s.url, sizeBytes: s.sizeBytes };
      if (s.status === "error") throw new Error("Export failed");
      await new Promise((r) => setTimeout(r, 1500));
    }
  };
  const pin = (id: string, v?: boolean) => {
    const curr = alerts.find((a) => a.alertId === id)?.pinned ?? false;
    return restPin(id, v ?? !curr);
  };
  const ack = (id: string, v?: boolean) => {
    const curr = alerts.find((a) => a.alertId === id)?.acknowledged ?? false;
    return restAck(id, v ?? !curr);
  };
  const bulkPin = (ids: string[]) => { ids.forEach((id) => restPin(id, true)); };
  const bulkAck = (ids: string[]) => { ids.forEach((id) => restAck(id, true)); };
  const setNote = (id: string, note: string) => { return restNote(id, note); };
  const clear = () => setAlerts([]);
  const clearAnimations = () => setAlerts((prev) => prev.map((a) => (a._animate ? { ...a, _animate: false } : a)));
  const setFilters = (next: Partial<LiveFilters>) => setFiltersState((prev) => {
    const merged = { ...prev, ...next } as LiveFilters;
    if (next.categories) merged.categories = new Set(next.categories);
    return merged;
  });
  const getVisible = () => sortAlerts(filterAlerts(alerts, filters), filters.sort);

  const setDevOptions = (next: Partial<DevOptions>) => setDev((prev) => ({ ...prev, ...next }));

  const queueBulkExport = (
    alertIds: string[],
    opts?: { concurrency?: number; onUpdate?: (u: { alertId: string; status: "queued" | "exporting" | "complete" | "error" | "cancelled"; url?: string; sizeBytes?: number; index: number; total: number }) => void }
  ) => {
    let cancelled = false;
    const concurrency = Math.max(1, opts?.concurrency ?? 2);
    const total = alertIds.length;
    let index = 0;
    const inFlight = new Set<number>();
    const cancel = () => { cancelled = true; };
    const start = () => new Promise<void>((resolve) => {
      const launchNext = () => {
        if (cancelled) { resolve(); return; }
        while (inFlight.size < concurrency && index < total) {
          const idx = index++;
          const alertId = alertIds[idx];
          inFlight.add(idx);
          opts?.onUpdate?.({ alertId, status: "exporting", index: idx, total });
          doExport(alertId)
            .then((exportId) => pollExport(exportId))
            .then(({ url, sizeBytes }) => {
              opts?.onUpdate?.({ alertId, status: "complete", url, sizeBytes, index: idx, total });
            })
            .catch(() => {
              if (!cancelled) opts?.onUpdate?.({ alertId, status: "error", index: idx, total });
            })
            .finally(() => {
              inFlight.delete(idx);
              if (index >= total && inFlight.size === 0) resolve();
              else launchNext();
            });
        }
      };
      launchNext();
    });
    return { cancel, start };
  };
  const value: LiveStoreState = {
    alerts,
    filters,
    dev,
    connection,
    addAlerts,
    pin,
    ack,
    bulkPin,
    bulkAck,
    setNote,
    clear,
    setFilters,
    getVisible,
    clearAnimations,
    setDevOptions,
    live: {
      connect: liveConnect,
      disconnect: liveDisconnect,
      fetchHistory,
      ack: restAck,
      pin: restPin,
      note: restNote,
      export: doExport,
      pollExport,
    },
    exportOne: doExport,
    pollExport,
    queueBulkExport,
  };

  return <LiveStoreCtx.Provider value={value}>{children}</LiveStoreCtx.Provider>;
};

export function useLiveStore() {
  const ctx = useContext(LiveStoreCtx);
  if (!ctx) throw new Error("useLiveStore must be used within LiveProvider");
  return ctx;
}
