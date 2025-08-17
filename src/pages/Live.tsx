import React from "react";
import { SEOHead } from "@/components/SEO";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Play, Pause, Volume2, VolumeX, Pin, Check, PinOff, Wifi, WifiOff, Loader2 } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useLiveStore, Category } from "@/context/LiveStore";
import { toast } from "@/components/ui/use-toast";
import { fetchLiveHistory } from "@/lib/liveHistory";
const ALL_CATEGORIES: Category[] = ["people", "color", "fire", "vehicle", "weapon", "activity"];

const LivePage: React.FC = () => {
  const [isPlaying, setIsPlaying] = React.useState(true);
  const [isMuted, setIsMuted] = React.useState(true);
  const navigate = useNavigate();

  const { getVisible, filters, setFilters, pin, ack, clearAnimations, addAlerts, live, connection, clear } = useLiveStore();
  const items = getVisible();

  // URL state for cameraId
  const [searchParams, setSearchParams] = useSearchParams();
  const onUpdateUrl = React.useCallback((next: Partial<{ cameraId: string | null }>) => {
    const nextParams = new URLSearchParams(searchParams);
    if ("cameraId" in next) {
      if (next.cameraId) nextParams.set("cameraId", next.cameraId);
      else nextParams.delete("cameraId");
    }
    setSearchParams(nextParams, { replace: true });
  }, [searchParams, setSearchParams]);

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
    // Connect to live API and fetch history on mount
    const cam = committedCameraRef.current;
    live.connect(cam || null);
    live.fetchHistory({ cameraId: cam || undefined, limit: 100 });

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

  // Apply cameraId from URL on history navigation (popstate)
  const didMountPop = React.useRef(false);
  React.useEffect(() => {
    if (!didMountPop.current) { didMountPop.current = true; return; }
    const cam = searchParams.get("cameraId") ?? "";
    if ((committedCameraRef.current || "") !== cam) {
      setCameraInput(cam);
      commitCamera(cam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

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
        list = await fetchLiveHistory({ cameraId: next, limit: 100, signal: abortRef.current.signal });
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

  const retriesLast30 = reconnectTimestampsRef.current.filter((t) => Date.now() - t < 30000).length;
  const isUnstable = connection === "unstable" || retriesLast30 > 1;
  
  // Clear animation flags shortly after mount/updates
  React.useEffect(() => {
    if (items.some((a) => a._animate)) {
      const id = setTimeout(() => clearAnimations(), 400);
      return () => clearTimeout(id);
    }
  }, [items, clearAnimations]);

  const toggleCategory = (c: Category) => {
    const next = new Set(filters.categories);
    if (next.has(c)) next.delete(c);
    else next.add(c);
    setFilters({ categories: next });
  };

  const clearAll = () => setFilters({ categories: new Set() });
  const selectCommon = () => setFilters({ categories: new Set(["people", "vehicle", "activity", "fire"]) });

  const pinned = items.filter((a) => a.pinned);
  const others = items.filter((a) => !a.pinned);

  const PlayerOverlay = (
    <div className="absolute inset-0 pointer-events-none flex items-start justify-between p-4">
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-destructive animate-pulse" aria-hidden />
        <span className="text-xs font-medium">LIVE</span>
      </div>
      <div className="text-xs opacity-70">Timeline disabled</div>
    </div>
  );

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
      <SEOHead title="Live – Surveillance AI" description="Live monitoring feed with real-time AI alerts." />
      {/* Live region for announcements */}
      <div className="sr-only" aria-live="polite">{items.length} alerts</div>
      <div className="sr-only" aria-live="polite">{statusLive}</div>
      {switching && (
        <div className="mb-3 rounded-md border bg-amber-100/40 text-amber-900 px-3 py-2 text-xs flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          <span>Switching camera…</span>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6">
        {/* Left: Player */}
        <section className="lg:col-span-8">
          <div className="relative overflow-hidden rounded-lg bg-gradient-to-br from-primary/10 to-secondary/10 aspect-video shadow-sm">
            {PlayerOverlay}
            {/* Fake player surface */}
            <div className="absolute inset-0 flex items-center justify-center select-none">
              <div className="text-sm md:text-base opacity-70">Placeholder live stream</div>
            </div>
            {/* Minimal controls */}
            <div className="absolute bottom-3 left-3 flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setIsPlaying((v) => !v)} aria-pressed={isPlaying} aria-label={isPlaying ? "Pause" : "Play"}>
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button size="sm" variant="secondary" onClick={() => setIsMuted((v) => !v)} aria-pressed={isMuted} aria-label={isMuted ? "Unmute" : "Mute"}>
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </section>

        {/* Right: Alerts */}
        <aside className="lg:col-span-4">
          {/* Sticky filters */}
          <div className="sticky top-0 z-10 -mt-1 pb-3 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex flex-wrap items-center gap-2">
              {ALL_CATEGORIES.map((k) => {
                const active = filters.categories.has(k);
                return (
                  <Button
                    key={k}
                    size="sm"
                    variant={active ? "secondary" : "outline"}
                    aria-pressed={active}
                    onClick={() => toggleCategory(k)}
                  >
                    {k.charAt(0).toUpperCase() + k.slice(1)}
                  </Button>
                );
              })}
                <div className="ml-auto flex items-center gap-2">
                  {/* Camera ID input + status */}
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

                  <Button size="sm" variant="ghost" onClick={() => navigate("/live/filters")}>Filters</Button>
                  <Button size="sm" variant="ghost" onClick={clearAll}>Clear</Button>
                  <Button size="sm" variant="ghost" onClick={selectCommon}>Common</Button>
                </div>
            </div>
          </div>

          {/* Pinned section */}
          {pinned.length > 0 && (
            <div className="space-y-2 mb-3">
              {pinned.map((a) => (
                <AlertCard key={a.alertId} a={a} onPin={() => pin(a.alertId)} onAck={() => ack(a.alertId)} onOpen={() => navigate(`/live/review/${a.alertId}`)} />
              ))}
            </div>
          )}

          {/* Others */}
          <div className="space-y-2">
            {others.map((a) => (
              <AlertCard key={a.alertId} a={a} onPin={() => pin(a.alertId)} onAck={() => ack(a.alertId)} animate={a._animate} onOpen={() => navigate(`/live/review/${a.alertId}`)} />
            ))}
          </div>
        </aside>
      </div>
    </main>
  );
};

const AlertCard: React.FC<{
  a: ReturnType<typeof useLiveStore>["alerts"][number];
  onPin: () => void;
  onAck: () => void;
  onOpen?: () => void;
  animate?: boolean;
}> = ({ a, onPin, onAck, onOpen, animate }) => {
  return (
    <Card
      className={`${animate ? "animate-slide-in-right motion-reduce:animate-none" : ""} ${a.acknowledged ? "opacity-80" : ""}`}
      tabIndex={0}
      role="article"
      aria-label={`Alert ${a.timestamp} ${a.category}`}
      onKeyDown={(e) => {
        if (e.key === " ") { e.preventDefault(); onPin(); }
        else if (e.key === "Enter") { onOpen?.(); }
        else if (e.key.toLowerCase() === "a") { onAck(); }
      }}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Left column: time + confidence */}
          <div className="min-w-[72px] text-xs">
            <div className="font-medium">{a.timestamp}</div>
            <div className="text-muted-foreground">{Math.round(a.confidence * 100)}%</div>
          </div>

          {/* Middle: labels */}
          <div className="flex-1">
            <div className="flex flex-wrap gap-1.5">
              {a.labels.map((t, i) => (
                <Badge key={i} variant="secondary">{t}</Badge>
              ))}
              {a.pinned && <Badge className="ml-1" variant="outline">Pinned</Badge>}
              {a.acknowledged && <Badge className="ml-1" variant="outline">Ack</Badge>}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1">
            <Button size="icon" variant="ghost" onClick={onPin} aria-label={a.pinned ? "Unpin" : "Pin"}>
              {a.pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
            </Button>
            <Button size="icon" variant="ghost" onClick={onAck} aria-label="Acknowledge">
              <Check className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LivePage;
