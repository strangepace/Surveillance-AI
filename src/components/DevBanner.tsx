import React from "react";
import { useLiveStore } from "@/context/LiveStore";
import { AlertTriangle, WifiOff, Info } from "lucide-react";
import { API_BASE, WS_BASE } from "@/lib/api";

const DevBanner: React.FC = () => {
  const { connection, dev } = useLiveStore();

  if (!API_BASE) {
    return (
      <div className="mb-3 rounded-md border bg-muted px-3 py-2 text-xs flex items-center gap-2">
        <Info className="h-4 w-4" aria-hidden />
        <span>API_BASE_URL not set — using relative API</span>
      </div>
    );
  }

  if (connection === "mock") {
    return (
      <div className="mb-3 rounded-md border bg-warning/10 text-warning-foreground px-3 py-2 text-xs flex items-center gap-2">
        <WifiOff className="h-4 w-4" aria-hidden />
        <span>Live API unavailable — using mock data</span>
      </div>
    );
  }

  // Validate WS_BASE if provided
  try {
    if (WS_BASE) new URL(WS_BASE);
  } catch {
    return (
      <div className="mb-3 rounded-md border bg-muted px-3 py-2 text-xs flex items-center gap-2">
        <Info className="h-4 w-4" aria-hidden />
        <span>WS disabled (invalid base URL)</span>
      </div>
    );
  }

  if (connection === "unstable") {
    return (
      <div className="mb-3 rounded-md border bg-amber-100/40 text-amber-900 px-3 py-2 text-xs flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" aria-hidden />
        <span>Connection unstable — attempting to reconnect…</span>
      </div>
    );
  }

  if (!dev.useRealApi) {
    return (
      <div className="mb-3 rounded-md border bg-muted px-3 py-2 text-xs">
        Using mock by developer setting
      </div>
    );
  }
  return null;
};

export default DevBanner;
