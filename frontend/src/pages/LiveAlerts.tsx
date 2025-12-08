import React, { useDeferredValue } from "react";
import { SEOHead } from "@/components/SEO";
import { useLiveStore, Category } from "@/context/LiveStore";
import DevBanner from "@/components/DevBanner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Check, Pin, PinOff, Search, Loader2, Wifi, WifiOff } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "@/components/ui/use-toast";
import { fetchLiveHistory } from "@/lib/liveHistory";
import LazyVideo from "@/components/LazyVideo";
const ALL_CATEGORIES: Category[] = ["people", "color", "fire", "vehicle", "weapon", "activity"];

type SortValue = "newest" | "oldest" | "confidence_asc" | "confidence_desc";

const sortOptions: { label: string; value: SortValue }[] = [
  { label: "Newest", value: "newest" },
  { label: "Oldest", value: "oldest" },
  { label: "Confidence ↑", value: "confidence_asc" },
  { label: "Confidence ↓", value: "confidence_desc" },
];

const LiveAlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const { getVisible, setFilters, filters, pin, ack, live, connection, addAlerts, clear } = useLiveStore();

  // URL state
  const [searchParams, setSearchParams] = useSearchParams();
  React.useEffect(() => {
    const f = searchParams.get("filters");
    const q = searchParams.get("q") ?? "";
    const sort = (searchParams.get("sort") as SortValue) ?? "newest";
    const confidence = searchParams.get("confidence"); // e.g., "20-95"
    const timeRange = (searchParams.get("timeRange") as any) || undefined;
    const cameraId = searchParams.get("cameraId");
    const nextCats = new Set<Category>();
    f?.split(",").forEach((x) => {
      if (ALL_CATEGORIES.includes(x as Category)) nextCats.add(x as Category);
    });
    const next: any = { categories: nextCats, search: q, sort };
    if (confidence && /^(\d{1,3})-(\d{1,3})$/.test(confidence)) {
      const [, lo, hi] = confidence.match(/(\d{1,3})-(\d{1,3})/)!;
      next.confidenceRange = [Math.max(0, Math.min(100, +lo)) / 100, Math.max(0, Math.min(100, +hi)) / 100];
    }
    if (timeRange) next.timeRange = timeRange;
    const last = (typeof window !== "undefined" ? localStorage.getItem("lastCameraId") : null) ||
      (import.meta as any)?.env?.NEXT_PUBLIC_DEFAULT_CAMERA_ID ||
      (import.meta as any)?.env?.VITE_DEFAULT_CAMERA_ID || "";
    if (cameraId !== null) next.cameraId = cameraId || null;
    else if (last) next.cameraId = last;
    setFilters(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onUpdateUrl = (next: Partial<{ filters: string; q: string; sort: SortValue; cameraId: string | null; sel: string }>) => {
    const nextParams = new URLSearchParams(searchParams);
    if (next.filters !== undefined) {
      if (next.filters) nextParams.set("filters", next.filters);
      else nextParams.delete("filters");
    }
    if (next.q !== undefined) {
      if (next.q) nextParams.set("q", next.q);
      else nextParams.delete("q");
    }
    if (next.sort !== undefined) {
      if (next.sort) nextParams.set("sort", next.sort);
      else nextParams.delete("sort");
    }
    if ("cameraId" in next) {
      if (next.cameraId) nextParams.set("cameraId", next.cameraId);
      else nextParams.delete("cameraId");
    }
    if (next.sel !== undefined) {
      if (next.sel) nextParams.set("sel", next.sel);
      else nextParams.delete("sel");
    }
    setSearchParams(nextParams, { replace: true });
  };

  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const items = getVisible();
  const deferredItems = useDeferredValue(items);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [hoverId, setHoverId] = React.useState<string | null>(null);
  const [focusedIdx, setFocusedIdx] = React.useState<number>(0);
  const selectionAnchorRef = React.useRef<number>(0);
  const previewTimerRef = React.useRef<number | null>(null);
  const previewCacheRef = React.useRef<Set<string>>(new Set());

  // Dynamic overscan by scroll speed + prewarm hover cache
  const [overscan, setOverscan] = React.useState<number>(10);
  const lastRef = React.useRef<{ t: number; y: number }>({ t: performance.now(), y: 0 });
  const rafRef = React.useRef<number | null>(null);
  React.useEffect(() => {
    const el = parentRef.current;
    if (!el) return;
    const onScroll = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const now = performance.now();
        const y = el.scrollTop;
        const dt = Math.max(1, now - lastRef.current.t);
        const dy = Math.abs(y - lastRef.current.y);
        const speed = dy / dt; // px/ms
        lastRef.current = { t: now, y };
        const approxRowsPerMs = speed / 96; // ~row height
        const target = Math.min(30, Math.max(6, Math.round(approxRowsPerMs * 120 + 8)));
        if (target !== overscan) setOverscan(target);
      });
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el.removeEventListener("scroll", onScroll as any);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [overscan]);

  React.useEffect(() => {
    const win: any = window as any;
    const cb = () => {
      deferredItems.slice(0, 3).forEach((a) => a?.alertId && previewCacheRef.current.add(a.alertId));
    };
    let id: any;
    if (win.requestIdleCallback) id = win.requestIdleCallback(cb, { timeout: 800 });
    else id = window.setTimeout(cb, 500);
    return () => {
      if (win.cancelIdleCallback && id) win.cancelIdleCallback(id);
      else clearTimeout(id);
    };
  }, [deferredItems.length]);
  // Camera control state and lifecycle
  const abortRef = React.useRef<AbortController | null>(null);
  const committedCameraRef = React.useRef<string | null>(null);
  const [cameraInput, setCameraInput] = React.useState<string>("");
  const [cameraError, setCameraError] = React.useState<string | null>(null);
  const [switching, setSwitching] = React.useState(false);
  const [statusLive, setStatusLive] = React.useState("");
  const [lastConnectedAt, setLastConnectedAt] = React.useState<number | null>(null);
  const reconnectTimestampsRef = React.useRef<number[]>([]);

  const initialCamera = React.useMemo(() => {
    const urlCam = searchParams.get("cameraId");
    if (urlCam !== null) return urlCam || "";
    const last = (typeof window !== "undefined" ? localStorage.getItem("lastCameraId") : null) ||
      (import.meta as any)?.env?.NEXT_PUBLIC_DEFAULT_CAMERA_ID ||
      (import.meta as any)?.env?.VITE_DEFAULT_CAMERA_ID || "";
    return last || "";
  }, []);

  React.useEffect(() => {
    setCameraInput((filters.cameraId ?? initialCamera ?? "") || "");
    committedCameraRef.current = filters.cameraId ?? (initialCamera || null);
    // Connect to live API and fetch history on mount with precedence
    const cam = committedCameraRef.current;
    live.connect(cam || null);
    const windowSec =
      filters.timeRange === "30s" ? 30 :
      filters.timeRange === "2m" ? 120 :
      filters.timeRange === "10m" ? 600 :
      filters.timeRange === "1h" ? 3600 : 86400;
    live.fetchHistory({ cameraId: cam || undefined, windowSec, limit: 200 });

    // focus restoration after returning from filters
    const sel = sessionStorage.getItem("live.returnFocus");
    if (sel) {
      sessionStorage.removeItem("live.returnFocus");
      setTimeout(() => {
        const el = document.querySelector(sel) as HTMLElement | null;
        el?.focus();
      }, 50);
    }

    return () => {
      abortRef.current?.abort();
      live.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Track connection metadata for indicator/tooltip
  React.useEffect(() => {
    if (connection === "connected") {
      const now = Date.now();
      setLastConnectedAt(now);
      setStatusLive(`Connected to ${committedCameraRef.current || "default"}`);
    }
    if (connection === "connecting") {
      const now = Date.now();
      reconnectTimestampsRef.current = [
        ...reconnectTimestampsRef.current.filter((t) => now - t < 30000),
        now,
      ];
    }
  }, [connection]);

  // Apply cameraId from URL on history navigation (popstate) and selection sync
  const didMountPop = React.useRef(false);
  React.useEffect(() => {
    if (!didMountPop.current) { didMountPop.current = true; }
    const cam = searchParams.get("cameraId") ?? "";
    if ((committedCameraRef.current || "") !== cam) {
      setCameraInput(cam);
      commitCamera(cam);
    }
    // Restore selection from URL
    const sel = searchParams.get("sel");
    if (sel !== null) {
      const set = new Set(sel ? sel.split(",") : []);
      setSelected(set);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const retriesLast30 = reconnectTimestampsRef.current.filter((t) => Date.now() - t < 30000).length;
  const isUnstable = connection === "unstable" || retriesLast30 > 1;

  // Reconnect when returning online/visible
  React.useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "visible") {
        live.connect(committedCameraRef.current || null);
      }
    };
    const onOnline = () => live.connect(committedCameraRef.current || null);
    window.addEventListener("visibilitychange", onVis);
    window.addEventListener("online", onOnline);
    return () => {
      window.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("online", onOnline);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isValidCamera = (v: string) => v.trim() === "" || /^[A-Za-z0-9_-]{1,32}$/.test(v.trim());

  async function commitCamera(nextRaw: string) {
    const next = nextRaw.trim();
    if (!isValidCamera(next)) {
      setCameraError("Invalid ID. Use 1–32 letters, numbers, _ or -");
      return;
    }
    setCameraError(null);
    const prev = committedCameraRef.current;
    if ((prev || "") === next) {
      // Still persist and sync URL/localStorage
      if (next) localStorage.setItem("lastCameraId", next);
      else localStorage.removeItem("lastCameraId");
      setFilters({ cameraId: next || null });
      onUpdateUrl({ cameraId: next || null });
      return;
    }

    if (next) localStorage.setItem("lastCameraId", next);
    else localStorage.removeItem("lastCameraId");
    setFilters({ cameraId: next || null });
    onUpdateUrl({ cameraId: next || null });

    // Cancel any in-flight history fetch
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setSwitching(true);
    setStatusLive("Switching camera…");
    toast({ title: "Switching camera…", description: next ? `Connecting to ${next}` : "Using default", });

    try {
      live.disconnect();
      committedCameraRef.current = next || null;
      live.connect(committedCameraRef.current || null);
      let list: any[] = [];
      if (next) {
        list = await fetchLiveHistory({ cameraId: next, limit: 200, signal: abortRef.current.signal });
      }
      clear();
      if (list.length) addAlerts(list as any);
      setSwitching(false);
      setStatusLive(`Connected to ${next || "default"}`);
      toast({ title: "Connected", description: `Connected to ${next || "default"}` });
    } catch (err: any) {
      if (err?.name === "AbortError") return;
      setSwitching(false);
      // restore previous
      committedCameraRef.current = prev;
      setCameraInput((prev || ""));
      setFilters({ cameraId: prev || null });
      onUpdateUrl({ cameraId: prev || null });
      live.disconnect();
      live.connect(prev || null);
      toast({ title: "Failed to switch", description: err?.message || "Unknown error", variant: "destructive" });
    }
  }


  const [searchVal, setSearchVal] = React.useState(filters.search);
  React.useEffect(() => { setSearchVal(filters.search); }, [filters.search]);
  React.useEffect(() => {
    const h = setTimeout(() => {
      setFilters({ search: searchVal });
      onUpdateUrl({ q: searchVal });
    }, 300);
    return () => clearTimeout(h);
  }, [searchVal]);

  // Deep-link: focus specific alertId via ?q=ALERTID
  React.useEffect(() => {
    const q = searchParams.get("q");
    if (!q) return;
    const idx = items.findIndex((a) => a.alertId === q);
    if (idx >= 0) {
      setFocusedIdx(idx);
      selectionAnchorRef.current = idx;
      setTimeout(() => {
        rowVirtualizer.scrollToIndex(idx);
        const el = document.getElementById(`row-${items[idx].alertId}`);
        el?.focus();
      }, 50);
    }
    const next = new URLSearchParams(searchParams);
    next.delete("q");
    setSearchParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items.length]);

  const rowVirtualizer = useVirtualizer({
    count: deferredItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 96,
    overscan,
  });

  // Toolbar handlers
  const toggleCategory = (c: Category) => {
    const next = new Set(filters.categories);
    if (next.has(c)) next.delete(c);
    else next.add(c);
    setFilters({ categories: next });
    onUpdateUrl({ filters: Array.from(next).join(",") });
  };
  const onSearch = (q: string) => {
    setSearchVal(q);
  };
  const onSort = (value: SortValue) => {
    setFilters({ sort: value });
    onUpdateUrl({ sort: value });
  };

  // Bulk actions
  const [bulkStatus, setBulkStatus] = React.useState("");
  const bulkPin = () => {
    selected.forEach((id) => pin(id, true));
    setBulkStatus(`Pinned ${selected.size} alerts`);
    setSelected(new Set());
  };
  const bulkAck = () => {
    selected.forEach((id) => ack(id, true));
    setBulkStatus(`Acknowledged ${selected.size} alerts`);
    setSelected(new Set());
  };

  // Indicator props
  const status = (isUnstable ? "unstable" : connection) as typeof connection | "unstable";
  const statusLabel = `Status: ${status}${lastConnectedAt ? ` • Last connected ${Math.round((Date.now() - lastConnectedAt) / 1000)}s ago` : ""} • Retries: ${retriesLast30}`;
  const indicatorClasses =
    status === "connected"
      ? "bg-emerald-100 text-emerald-900"
      : status === "connecting"
      ? "bg-amber-100 text-amber-900"
      : status === "unstable"
      ? "bg-amber-100 text-amber-900 animate-pulse"
      : status === "mock"
      ? "bg-purple-100 text-purple-900"
      : "bg-muted text-muted-foreground";

  return (
    <main className="container mx-auto p-4 md:p-6">
      <SEOHead title="Live Alerts – Surveillance AI" description="Live alerts feed with search, filters, and bulk actions." />
      <h1 className="text-xl font-semibold mb-3">Live Alerts</h1>
      <DevBanner />

      {switching && (
        <div className="mb-3 rounded-md border bg-amber-100/40 text-amber-900 px-3 py-2 text-xs flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          <span>Switching camera…</span>
        </div>
      )}

      {/* Toolbar */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b py-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-full md:w-80">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 opacity-60" />
            <Input
              placeholder="Search labels, category…"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              className="pl-8"
            />
          </div>

          {/* Category chips */}
          <div className="flex flex-wrap items-center gap-2">
            {ALL_CATEGORIES.map((c) => (
              <Button key={c} size="sm" variant={filters.categories.has(c) ? "secondary" : "outline"} onClick={() => toggleCategory(c)}>
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </Button>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Select value={filters.sort} onValueChange={(v) => onSort(v as SortValue)}>
              <SelectTrigger className="w-[180px]"><SelectValue placeholder="Sort" /></SelectTrigger>
              <SelectContent>
                {sortOptions.map((o) => (
                  <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selected.size > 0 && (
              <div className="flex items-center gap-2" aria-live="polite">
                <Button size="sm" variant="outline" onClick={bulkPin}><Pin className="h-4 w-4 mr-1" /> Pin</Button>
                <Button size="sm" variant="outline" onClick={bulkAck}><Check className="h-4 w-4 mr-1" /> Acknowledge</Button>
                <span className="text-xs text-muted-foreground">{selected.size} selected</span>
              </div>
            )}

            {/* Camera ID input */}
            <div className="flex flex-col items-start gap-1">
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Camera ID"
                  value={cameraInput}
                  onChange={(e) => setCameraInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") commitCamera(cameraInput);
                    else if (e.key === "Escape") { setCameraInput((committedCameraRef.current || "")); setCameraError(null); }
                  }}
                  onBlur={() => commitCamera(cameraInput)}
                  className="w-[160px]"
                  aria-invalid={!!cameraError}
                  aria-describedby={cameraError ? "camera-error" : undefined}
                />
                {/* Status pill with tooltip */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={`px-2 py-1 rounded-full text-xs leading-none select-none ${indicatorClasses}`} aria-label={statusLabel} role="status">
                        {status === "connected" ? <Wifi className="h-3.5 w-3.5 inline mr-1" /> : status === "connecting" ? <Loader2 className="h-3.5 w-3.5 inline mr-1 animate-spin" /> : status === "unstable" ? <Wifi className="h-3.5 w-3.5 inline mr-1 animate-pulse" /> : status === "mock" ? <Wifi className="h-3.5 w-3.5 inline mr-1" /> : <WifiOff className="h-3.5 w-3.5 inline mr-1" />}
                        {status}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{statusLabel}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <Button size="sm" variant="outline" onClick={() => { live.disconnect(); live.connect(committedCameraRef.current || null); }} disabled={connection === "connecting" || switching} aria-label={`Reconnect (${status})`}>
                  Reconnect
                </Button>
              </div>
              {cameraError && <div id="camera-error" className="text-xs text-destructive">{cameraError}</div>}
            </div>

            <Button size="sm" variant="ghost" onClick={() => { try { const active = document.activeElement as HTMLElement | null; let sel = "#alerts-list"; if (active) { const row = active.closest("[data-rowid]") as HTMLElement | null; if (row?.id) sel = `#${row.id}`; } sessionStorage.setItem("live.returnFocus", sel); } catch {} navigate("/live/filters"); }}>Filters</Button>
          </div>
        </div>
      </div>

      {/* Live region for announcements */}
      <div className="sr-only" aria-live="polite">{items.length} alerts</div>
      <div className="sr-only" aria-live="polite">{statusLive}</div>
      <div className="sr-only" aria-live="polite">{bulkStatus}</div>

      {/* List */}
      <div
        ref={parentRef}
        id="alerts-list"
        role="list"
        aria-label="Live alerts"
        className="h-[72vh] overflow-auto rounded-md border mt-3"
        onKeyDown={(e) => {
          const tag = (document.activeElement as HTMLElement | null)?.tagName?.toLowerCase();
          if (tag === "input" || tag === "textarea") return;
          const list = deferredItems;
          if (!list.length) return;
          if (e.key.toLowerCase() === "j") {
            e.preventDefault();
            const next = Math.min(list.length - 1, focusedIdx + 1);
            setFocusedIdx(next);
            selectionAnchorRef.current = next;
            const el = document.getElementById(`row-${list[next]?.alertId}`);
            el?.focus();
            rowVirtualizer.scrollToIndex(next);
          } else if (e.key.toLowerCase() === "k") {
            e.preventDefault();
            const next = Math.max(0, focusedIdx - 1);
            setFocusedIdx(next);
            selectionAnchorRef.current = next;
            const el = document.getElementById(`row-${list[next]?.alertId}`);
            el?.focus();
            rowVirtualizer.scrollToIndex(next);
          } else if (e.key.toLowerCase() === "a") {
            const id = list[focusedIdx]?.alertId; if (id) ack(id);
          } else if (e.key.toLowerCase() === "p") {
            const id = list[focusedIdx]?.alertId; if (id) pin(id);
          } else if (e.key === "Enter") {
            const id = list[focusedIdx]?.alertId; if (id) navigate(`/live/review/${id}`);
          } else if (e.key === "ArrowDown" && e.shiftKey) {
            e.preventDefault();
            const end = Math.min(list.length - 1, focusedIdx + 1);
            const start = selectionAnchorRef.current;
            const nextSel = new Set<string>(selected);
            for (let i = Math.min(start, end); i <= Math.max(start, end); i++) nextSel.add(list[i].alertId);
            setSelected(nextSel);
            setFocusedIdx(end);
            const el = document.getElementById(`row-${list[end]?.alertId}`); el?.focus();
            rowVirtualizer.scrollToIndex(end);
          } else if (e.key === "ArrowUp" && e.shiftKey) {
            e.preventDefault();
            const end = Math.max(0, focusedIdx - 1);
            const start = selectionAnchorRef.current;
            const nextSel = new Set<string>(selected);
            for (let i = Math.min(start, end); i <= Math.max(start, end); i++) nextSel.add(list[i].alertId);
            setSelected(nextSel);
            setFocusedIdx(end);
            const el = document.getElementById(`row-${list[end]?.alertId}`); el?.focus();
            rowVirtualizer.scrollToIndex(end);
          }
        }}
      >
        <div style={{ height: rowVirtualizer.getTotalSize(), position: "relative" }}>
          {rowVirtualizer.getVirtualItems().map((vi) => {
            const i = vi.index;
            const a = deferredItems[i];
            const isSel = selected.has(a.alertId);
            const isHover = hoverId === a.alertId;
            return (
              <div key={vi.key} style={{ transform: `translateY(${vi.start}px)`, position: "absolute", left: 0, right: 0 }} className="p-2" role="listitem">
                <Card
                  id={`row-${a.alertId}`}
                  className={`relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md ${a.pinned ? "ring-1 ring-primary/30" : ""} ${a.acknowledged ? "opacity-80" : ""}`}
                  tabIndex={focusedIdx === i ? 0 : -1}
                  role="article"
                  aria-label={`Alert ${a.timestamp} ${a.labels.slice(0,2).join(", ")}`}
                  aria-selected={isSel}
                  onFocus={() => { setFocusedIdx(i); selectionAnchorRef.current = i; }}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3"
                      onMouseEnter={() => {
                        if (previewTimerRef.current) window.clearTimeout(previewTimerRef.current);
                        previewTimerRef.current = window.setTimeout(() => {
                          setHoverId(a.alertId);
                          previewCacheRef.current.add(a.alertId);
                          if (previewCacheRef.current.size > 12) {
                            const first = previewCacheRef.current.values().next().value;
                            previewCacheRef.current.delete(first);
                          }
                        }, 120);
                      }}
                      onMouseLeave={() => {
                        if (previewTimerRef.current) window.clearTimeout(previewTimerRef.current);
                        setHoverId(null);
                      }}
                    >
                      {/* Thumb / Preview */}
                      <div className="h-14 w-20 rounded-md overflow-hidden border shrink-0">
                        {isHover || previewCacheRef.current.has(a.alertId) ? (
                          <LazyVideo src={a.clipUrl || ""} autoPlay muted loop playsInline pauseOffscreen className="h-full w-full object-cover" />
                        ) : (
                          <img src={a.thumbnailUrl || "/placeholder.svg"} alt={`Alert ${a.alertId} thumbnail`} loading="lazy" className="h-full w-full object-cover" />
                        )}
                      </div>

                      {/* Middle */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <div className="text-xs text-muted-foreground w-20 shrink-0">{a.timestamp}</div>
                          <Badge variant="secondary">{a.category}</Badge>
                          <span className="text-xs opacity-70">{Math.round(a.confidence * 100)}%</span>
                        </div>
                        <div className="mt-1 flex flex-wrap gap-1.5">
                          {a.labels.slice(0, 3).map((t, k) => (
                            <Badge key={k} variant="outline">{t}</Badge>
                          ))}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1">
                        <input
                          type="checkbox"
                          aria-label="Select row"
                          checked={isSel}
                          onChange={(e) => {
                            const next = new Set(selected);
                            if (e.target.checked) next.add(a.alertId);
                            else next.delete(a.alertId);
                            setSelected(next);
                            onUpdateUrl({ sel: Array.from(next).join(",") });
                          }}
                          className="mr-2"
                        />
                        <Button size="icon" variant="ghost" onClick={() => pin(a.alertId)} aria-label={a.pinned ? "Unpin" : "Pin"} aria-pressed={a.pinned}>
                          {a.pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
                        </Button>
                        <Button size="icon" variant="ghost" onClick={() => ack(a.alertId)} aria-label="Acknowledge" aria-checked={a.acknowledged} role="checkbox">
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => navigate(`/live/review/${a.alertId}`)}>Open</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
};

export default LiveAlertsPage;
