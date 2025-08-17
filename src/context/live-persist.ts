import { Alert } from "./live-types";

const STORAGE_KEY = "live.alerts.v1";

export function loadAlerts(): Alert[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr: Alert[] = JSON.parse(raw);
    return Array.isArray(arr) ? arr.slice(0, 500) : [];
  } catch {
    return [];
  }
}

let idleSaveHandle: number | undefined;
export function saveAlertsIdle(alerts: Alert[]) {
  const save = () => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts.slice(0, 500))); } catch {}
  };
  const rif = (window as any).requestIdleCallback as undefined | ((cb: () => void, opts?: any) => number);
  if (rif) {
    if (idleSaveHandle) (window as any).cancelIdleCallback?.(idleSaveHandle);
    idleSaveHandle = rif(save, { timeout: 1000 });
  } else {
    // fallback microtask
    Promise.resolve().then(save);
  }
}

export type DevOptionsPersist = { simCategories: any; jitterFps: boolean; useRealApi?: boolean };

export function loadDev(): DevOptionsPersist | null {
  try {
    const raw = localStorage.getItem("dev.live.simCats");
    const jitter = localStorage.getItem("dev.live.jitterFps") === "1";
    const useRealApi = localStorage.getItem("dev.live.useRealApi");
    const sim = raw ? JSON.parse(raw) : {};
    return { simCategories: sim?.simCategories ?? sim ?? {}, jitterFps: jitter, useRealApi: useRealApi !== "0" };
  } catch {
    return null;
  }
}

export function saveDev(opts: DevOptionsPersist) {
  try {
    localStorage.setItem("dev.live.simCats", JSON.stringify({ simCategories: opts.simCategories }));
    localStorage.setItem("dev.live.jitterFps", opts.jitterFps ? "1" : "0");
    if (opts.useRealApi !== undefined) localStorage.setItem("dev.live.useRealApi", opts.useRealApi ? "1" : "0");
  } catch {}
}
