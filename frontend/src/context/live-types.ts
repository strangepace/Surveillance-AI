export type Category = "people" | "color" | "fire" | "vehicle" | "weapon" | "activity";

export type Alert = {
  alertId: string;
  cameraId: string;
  tsUnix: number; // epoch seconds
  timestamp: string; // human-readable
  labels: string[];
  category: Category;
  confidence: number; // 0..1
  thumbnailUrl?: string;
  clipUrl?: string;
  location?: { lat: number; lng: number };
  pinned: boolean;
  acknowledged: boolean;
  note?: string;
  _animate?: boolean; // transient UI flag
};

export type SortKey = "newest" | "oldest" | "confidence_asc" | "confidence_desc";

export type LiveFilters = {
  categories: Set<Category>;
  search: string;
  sort: SortKey;
  confidenceRange: [number, number];
  timeRange: "30s" | "2m" | "10m" | "1h" | "24h" | "custom";
  cameraId?: string | null;
};

export type DevOptions = {
  simCategories: Record<Category, boolean>;
  jitterFps: boolean;
  useRealApi: boolean; // new toggle
};

export type ConnectionStatus = "idle" | "connecting" | "connected" | "unstable" | "disconnected" | "error" | "mock";

export type LiveStoreState = {
  alerts: Alert[];
  filters: LiveFilters;
  dev: DevOptions;
  connection: ConnectionStatus;
  // base ops
  addAlerts: (list: Alert[]) => void;
  pin: (id: string, v?: boolean) => void;
  ack: (id: string, v?: boolean) => void;
  bulkPin: (ids: string[]) => void;
  bulkAck: (ids: string[]) => void;
  setNote: (id: string, note: string) => void;
  clear: () => void;
  setFilters: (next: Partial<LiveFilters>) => void;
  getVisible: () => Alert[];
  clearAnimations: () => void;
  setDevOptions: (next: Partial<DevOptions>) => void;
  // API actions
  live: {
    connect: (cameraId?: string | null) => void;
    disconnect: () => void;
    fetchHistory: (params?: { cameraId?: string; since?: number; limit?: number }) => Promise<void>;
    ack: (alertId: string, acknowledged: boolean) => Promise<void>;
    pin: (alertId: string, pinned: boolean) => Promise<void>;
    note: (alertId: string, note: string) => Promise<void>;
    export: (alertId: string) => Promise<string>;
    pollExport: (exportId: string) => Promise<{ url?: string; sizeBytes?: number }>;
  };
  // New helpers (top-level exposure)
  exportOne?: (alertId: string) => Promise<string>;
  pollExport?: (exportId: string) => Promise<{ url?: string; sizeBytes?: number }>;
  queueBulkExport?: (
    alertIds: string[],
    opts?: {
      concurrency?: number;
      onUpdate?: (u: { alertId: string; status: "queued" | "exporting" | "complete" | "error" | "cancelled"; url?: string; sizeBytes?: number; index: number; total: number }) => void;
    }
  ) => { cancel: () => void; start: () => Promise<void> };
};
