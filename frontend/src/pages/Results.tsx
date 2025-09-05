import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { SEOHead } from "@/components/SEO";
import { useUpload } from "@/context/UploadContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { Download, FileJson, Filter, Pin, PinOff, CheckCircle2, PlayCircle } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";
import LazyVideo from "@/components/LazyVideo";
import { VirtualizedList } from "@/components/VirtualizedList";
import api from "@/lib/api";
// Types matching the provided mock JSON
export type ResultEntry = {
  timestamp: string;
  labels: string[];
  confidence: number; // 0..1
  preview_clip: string;
  preview_clip_mp4?: string; // MP4 preview URL
  preview_clip_webm?: string; // WebM preview URL (fallback)
  frame_index?: number; // for cache busting
};

export type AnalysisResponse = {
  status: string;
  video_id: string;
  results: ResultEntry[];
  alert_summary?: any; // Backend may return nested objects (e.g., priorities, categories)
  analysis_timestamp?: string;
  json_path?: string;
};

const CATEGORY_PATTERNS: Record<string, RegExp[]> = {
  people: [/person|man|woman|boy|girl|people|elderly/i],
  color: [/red|blue|green|yellow|black|white|orange|purple|pink|brown|gray|grey/i],
  fire: [/fire|smoke|flame/i],
  vehicles: [/car|vehicle|bus|truck|van|bike|bicycle|motorcycle|scooter/i],
};

const COMMON_FILTERS = ["people", "fire", "vehicles"];

const formatConf = (n: number) => `${Math.round(n * 100)}%`;

const ResultsPage: React.FC = () => {
  const { jobId } = useUpload();
  const [searchParams, setSearchParams] = useSearchParams();
  const jid = searchParams.get("jobId") || jobId || "";

  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [pinned, setPinned] = useState<Set<number>>(new Set());
  const [acknowledged, setAcknowledged] = useState<Set<number>>(new Set());

  const [exporting, setExporting] = useState(false);
  const [zoom, setZoom] = useState(1);
  const initRef = useRef(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  const timelineRef = useRef<HTMLDivElement | null>(null);

  // Guardrail: require jobId
  useEffect(() => {
    if (!jid) {
      toast({ title: "Missing job", description: "Redirecting to upload" });
      navigate("/upload", { replace: true });
    }
  }, [jid, navigate, toast]);

  // Keep URL in sync with context jobId
  useEffect(() => {
    if (jobId && !searchParams.get("jobId")) {
      const next = new URLSearchParams(searchParams);
      next.set("jobId", jobId);
      setSearchParams(next, { replace: true });
    }
  }, [jobId, searchParams, setSearchParams]);

useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!jid) {
        setError("Missing jobId. Please start a new analysis.");
        return;
      }
      setLoading(true);
      setError(null);
      const slow = localStorage.getItem("dev.slowMode") === "1";
      const mock = localStorage.getItem("dev.mockResults") === "1";
      const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));
      try {
        if (slow) await delay(2000 + Math.floor(Math.random() * 2000));
        let json: AnalysisResponse;
        if (mock) {
          const res = await fetch(`${window.location.origin}/mock/results-sample.json`);
          if (!res.ok) throw new Error(`Failed to fetch results (${res.status})`);
          json = (await res.json()) as AnalysisResponse;
        } else {
          json = await api.getResults(jid);
        }
        if (!cancelled) {
          setData(json);
          setSelectedIdx(json.results?.length ? 0 : null);
        }
        } catch (e: any) {
          if (!cancelled) {
            const msg = e?.message || "Unable to load results";
            setError(msg);
            const status = Number(e?.status || 0);
            const title = status >= 500 ? "Server error" : status >= 400 ? "Request error" : (e?.code === "NETWORK_ERROR" || status === 0) ? "Network error" : "Error";
            toast({ title, description: msg, variant: "destructive" });
          }
        } finally {
        if (!cancelled) setLoading(false);
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [jid]);

  // Initialize from URL/localStorage once
  useEffect(() => {
    if (initRef.current) return;
    const filtersParam = searchParams.get("filters");
    if (filtersParam) setActiveFilters(filtersParam.split(",").filter(Boolean));
    else {
      const saved = localStorage.getItem("results.filters");
      if (saved) {
        try {
          setActiveFilters(JSON.parse(saved));
        } catch {}
      }
    }
    initRef.current = true;
  }, [searchParams]);

// Persist filters to URL + localStorage (debounced)
useEffect(() => {
  const t = setTimeout(() => {
    const next = new URLSearchParams(searchParams);
    if (activeFilters.length) next.set("filters", activeFilters.join(","));
    else next.delete("filters");
    setSearchParams(next, { replace: true });
    try { localStorage.setItem("results.filters", JSON.stringify(activeFilters)); } catch {}
  }, 200);
  return () => clearTimeout(t);
}, [activeFilters, searchParams, setSearchParams]);

  const filteredResults = useMemo(() => {
    if (!data?.results) return [] as ResultEntry[];
    if (activeFilters.length === 0) return data.results;
    return data.results.filter((r) => {
      const text = r.labels.join(" ");
      return activeFilters.some((cat) => {
        const pats = CATEGORY_PATTERNS[cat] || [];
        return pats.some((re) => re.test(text));
      });
    });
  }, [data, activeFilters]);

const selected = useMemo(() => {
  if (selectedIdx == null) return null;
  const list = filteredResults.length ? filteredResults : data?.results || [];
  return list[selectedIdx] || null;
}, [filteredResults, data, selectedIdx]);

// Refs and helpers
const markerRefs = useRef<Array<HTMLButtonElement | null>>([]);
const toSeconds = useCallback((ts: string) => {
  const parts = ts.split(":").map(Number).filter((n) => !Number.isNaN(n));
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return Number(ts) || 0;
}, []);

const rawList = useMemo(() => (filteredResults.length ? filteredResults : data?.results || []), [filteredResults, data]);

// Build timeline items with simple clustering under high density
const timelineItems = useMemo(() => {
  const list = rawList;
  const maxMarkers = Math.max(30, Math.round(120 * zoom));
  if (list.length <= maxMarkers) {
    return list.map((r, i) => ({ type: "marker" as const, index: i, r }));
  }
  const clusterSize = Math.ceil(list.length / maxMarkers);
  const clusters: Array<{ type: "cluster"; start: number; end: number; count: number }> = [];
  for (let s = 0; s < list.length; s += clusterSize) {
    const e = Math.min(list.length - 1, s + clusterSize - 1);
    clusters.push({ type: "cluster", start: s, end: e, count: e - s + 1 });
  }
  return clusters;
}, [rawList, zoom]);

// Focus nearest marker when selection changes
useEffect(() => {
  if (selectedIdx == null) return;
  const el = markerRefs.current[selectedIdx];
  el?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
}, [selectedIdx]);

  // Sync selected timestamp in URL
  useEffect(() => {
    if (!data?.results) return;
    const next = new URLSearchParams(searchParams);
    if (selected) next.set("ts", selected.timestamp);
    else next.delete("ts");
    setSearchParams(next, { replace: true });
  }, [selected, data, searchParams, setSearchParams]);

// On load, if ts provided, select nearest result
useEffect(() => {
  if (!data?.results) return;
  const ts = searchParams.get("ts");
  if (!ts) return;
  const list = rawList;
  // find nearest by absolute time difference
  const target = toSeconds(ts);
  let bestIdx = 0;
  let bestDist = Infinity;
  list.forEach((r, i) => {
    const d = Math.abs(toSeconds(r.timestamp) - target);
    if (d < bestDist) { bestDist = d; bestIdx = i; }
  });
  setSelectedIdx(bestIdx);
}, [data, searchParams, rawList, toSeconds]);

  const handleToggleFilter = (key: string) => {
    setActiveFilters((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handlePin = (i: number) => {
    setPinned((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  const handleAck = (i: number) => {
    setAcknowledged((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  const handleDownloadJson = () => {
    if (data?.json_path) {
      window.open(data.json_path, "_blank");
    } else {
      toast({
        title: "JSON unavailable",
        description: "No json_path found in the results.",
      });
    }
  };

const handleExportClips = async () => {
    if (!jid || exporting) return;
    const human = (bytes: number) => {
      const units = ["B","KB","MB","GB"]; let u=0; let n=bytes;
      while (n >= 1024 && u < units.length-1) { n/=1024; u++; }
      return `${n.toFixed(1)} ${units[u]}`;
    };
    try {
      setExporting(true);
      toast({ title: "Preparing export", description: "Starting export…" });
      const { exportId } = await api.postExportClips(jid);
      toast({ title: "Export started", description: "We are preparing a ZIP with all preview clips." });
      let done = false;
      while (!done) {
        const status = await api.getExportStatus(exportId);
        if (status.status === "complete" && status.url) {
          const sizeText = status.sizeBytes ? ` (${human(status.sizeBytes)})` : "";
          toast({ title: "Export ready", description: `Download will start shortly${sizeText}.` });
          try {
            const a = document.createElement('a');
            a.href = status.url; a.download = "clips.zip"; a.rel = "noopener"; a.target = "_blank";
            document.body.appendChild(a); a.click(); a.remove();
          } catch {
            window.open(status.url, "_blank");
          }
          done = true;
          break;
        } else if (status.status === "error") {
          throw new Error("Export failed on server");
        }
        await new Promise((r) => setTimeout(r, 1000));
      }
    } catch (e: any) {
      toast({ title: "Export failed", description: e?.message || "Could not start export. Please try again." });
    } finally {
      setExporting(false);
    }
  };

  return (
    <main className="min-h-screen page-results-bg">
      <SEOHead
        title="Results – Surveillance AI"
        description="AI analysis results with timeline, filters, and export options."
      />

      <section className="mx-auto w-full max-w-7xl px-4 py-8 md:py-10">
        <header className="mb-6 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Results</h1>
            <p className="text-sm text-muted-foreground">
              {data?.analysis_timestamp
                ? new Date(data.analysis_timestamp).toLocaleString()
                : "Review the detections from your analysis."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => navigate("/configure")}>Configure</Button>
            <Button variant="secondary" onClick={() => navigate("/progress?jobId=" + encodeURIComponent(jid))}>
              <PlayCircle className="mr-2" /> Progress
            </Button>
          </div>
        </header>

        {/* Guardrails */}
        {error && (
          <Card className="animate-fade-in">
            <CardHeader>
              <CardTitle>Results unavailable</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={() => window.location.reload()}>Retry</Button>
                <Button variant="outline" onClick={() => navigate("/upload")}>Start new upload</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {!error && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="grid gap-4 md:grid-cols-12">
              <Card className="md:col-span-8 animate-fade-in">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Timeline</CardTitle>
                      <CardDescription>
                        Scrub through detections. Hover markers to preview.
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)))} aria-label="Zoom out">−</Button>
                      <Button size="sm" variant="outline" onClick={() => setZoom((z) => Math.min(2, +(z + 0.25).toFixed(2)))} aria-label="Zoom in">+</Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="w-full whitespace-nowrap">
                    <div ref={timelineRef} className="relative h-20 min-w-[640px]">
                      <div className="absolute left-0 right-0 top-1/2 h-px -translate-y-1/2 bg-border" />
                      <div className="relative flex h-full items-center px-2" style={{ gap: `${Math.round(12 * zoom)}px` }}>
                        {timelineItems.map((item, idx) => {
                          if ((item as any).type === "marker") {
                            const { index, r } = item as any;
                            return (
                              <Tooltip key={`${r.timestamp}-${index}`}>
                                <TooltipTrigger asChild>
                                  <button
                                    ref={(el) => (markerRefs.current[index] = el)}
                                    className={`h-4 w-4 rounded-full border transition-transform hover:scale-110 motion-reduce:transform-none motion-reduce:transition-none ${
                                      index === selectedIdx ? "bg-primary ring-2 ring-primary/50" : "bg-secondary"
                                    } ${pinned.has(index) ? "border-primary" : ""}`}
                                    aria-label={`Go to ${r.timestamp}`}
                                    onClick={() => setSelectedIdx(index)}
                                  />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <div className="text-xs w-56">
                                    <div className="font-medium mb-2">{r.timestamp}</div>
                                    <div className="overflow-hidden rounded border">
                                      <LazyVideo
                                        src={r.preview_clip}
                                        previewClipMp4={r.preview_clip_mp4}
                                        previewClipWebm={r.preview_clip_webm}
                                        muted
                                        playsInline
                                        preload="none"
                                        autoPlay
                                        loop
                                        className="w-full h-28 object-cover bg-secondary"
                                        aria-label={`Preview clip for ${r.timestamp}`}
                                        jobId={jid}
                                        frameIndex={r.frame_index}
                                      />
                                    </div>
                                    <div className="mt-2 flex flex-wrap gap-1">
                                      {r.labels.slice(0, 2).map((l, k) => (
                                        <Badge key={k} variant="secondary">{l}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                </TooltipContent>
                              </Tooltip>
                            );
                          }
                          const c = item as any;
                          const mid = Math.floor((c.start + c.end) / 2);
                          return (
                            <button
                              key={`cluster-${c.start}-${c.end}`}
                              className="h-6 px-2 rounded-full border bg-muted text-xs text-foreground/80 hover:bg-accent hover:text-accent-foreground"
                              onClick={() => setSelectedIdx(mid)}
                              aria-label={`Cluster of ${c.count} detections`}
                              title={`${c.count} detections`}
                            >
                              {c.count}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                    <ScrollBar orientation="horizontal" />
                  </ScrollArea>

                  {selected && (
                    <div className="mt-6 grid gap-4 md:grid-cols-12">
                      <div className="md:col-span-7">
                          <div className="overflow-hidden rounded-lg border">
                            <LazyVideo
                              src={selected.preview_clip}
                              previewClipMp4={selected.preview_clip_mp4}
                              previewClipWebm={selected.preview_clip_webm}
                              controls
                              className="h-auto w-full"
                              preload="metadata"
                              jobId={jid}
                              frameIndex={selected.frame_index}
                            />
                          </div>
                      </div>
                      <div className="md:col-span-5">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="text-sm text-muted-foreground">Timestamp</div>
                            <div className="font-medium">{selected.timestamp}</div>
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="text-sm text-muted-foreground">Confidence</div>
                            <div className="font-medium">{formatConf(selected.confidence)}</div>
                          </div>
                          <div>
                            <div className="mb-2 text-sm text-muted-foreground">Labels</div>
                            <div className="flex flex-wrap gap-2">
                              {selected.labels.map((l, k) => (
                                <Badge key={k} variant="outline">{l}</Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex gap-2 pt-2">
                            <Button
                              variant={pinned.has(selectedIdx ?? -1) ? "secondary" : "outline"}
                              onClick={() => selectedIdx != null && handlePin(selectedIdx)}
                            >
                              {pinned.has(selectedIdx ?? -1) ? <PinOff className="mr-2" /> : <Pin className="mr-2" />}
                              {pinned.has(selectedIdx ?? -1) ? "Unpin" : "Pin"}
                            </Button>
                            <Button
                              variant={acknowledged.has(selectedIdx ?? -1) ? "secondary" : "outline"}
                              onClick={() => selectedIdx != null && handleAck(selectedIdx)}
                            >
                              <CheckCircle2 className="mr-2" />
                              {acknowledged.has(selectedIdx ?? -1) ? "Acknowledged" : "Acknowledge"}
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="md:col-span-4 md:sticky md:top-4 animate-fade-in">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2">
                    <Filter /> Filters
                  </CardTitle>
                  <CardDescription>Refine which detections to display.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 sticky top-2 z-10 bg-background/60 backdrop-blur supports-[backdrop-filter]:bg-background/50 p-1 rounded-md">
                    {Object.keys(CATEGORY_PATTERNS).map((key) => (
                      <button
                        key={key}
                        onClick={() => handleToggleFilter(key)}
                        className={`inline-flex items-center rounded-full border px-3 py-1 text-sm transition-colors ${
                          activeFilters.includes(key)
                            ? "bg-secondary text-secondary-foreground"
                            : "bg-background hover:bg-accent hover:text-accent-foreground"
                        }`}
                      >
                        {key}
                      </button>
                    ))}
                    <div className="ml-auto flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => setActiveFilters(COMMON_FILTERS)}>
                        Select common
                      </Button>
                      {activeFilters.length > 0 && (
                        <Button variant="ghost" size="sm" onClick={() => setActiveFilters([])}>Clear all</Button>
                      )}
                    </div>
                  </div>

                  {data?.alert_summary && (
                    <div className="mt-6 space-y-2">
                      <div className="text-sm text-muted-foreground">Alert summary</div>
                      <div className="flex flex-wrap gap-2">
                        {/* Support both flat and nested summary shapes */}
                        {(() => {
                          const badges: Array<{ key: string; label: string }> = [];
                          const s: any = data.alert_summary || {};
                          if (typeof s.total_detections === "number") {
                            badges.push({ key: "total_detections", label: `total: ${s.total_detections}` });
                          }
                          if (s.priorities && typeof s.priorities === "object") {
                            for (const [k, v] of Object.entries(s.priorities)) {
                              if (typeof v === "number") badges.push({ key: `prio-${k}`, label: `${k}: ${v}` });
                            }
                          }
                          if (s.categories && typeof s.categories === "object") {
                            for (const [k, v] of Object.entries(s.categories)) {
                              if (typeof v === "number") badges.push({ key: `cat-${k}`, label: `${k}: ${v}` });
                            }
                          }
                          // Fallback for any remaining flat numeric fields
                          for (const [k, v] of Object.entries(s)) {
                            if (typeof v === "number" && !badges.find(b => b.key === k)) {
                              badges.push({ key: k, label: `${k}: ${v}` });
                            }
                          }
                          return badges.map(({ key, label }) => (
                            <Badge key={key} variant="secondary">{label}</Badge>
                          ));
                        })()}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Results list */}
            <div className="space-y-3">
              <h2 className="text-lg font-semibold tracking-tight">Detections</h2>
              {loading ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {Array.from({ length: 6 }).map((_, idx) => (
                    <Card key={`skeleton-${idx}`} className="relative">
                      <CardHeader className="space-y-1 pb-2">
                        <Skeleton className="h-4 w-1/3" />
                        <Skeleton className="h-4 w-1/4" />
                      </CardHeader>
                      <CardContent>
                        <Skeleton className="h-40 w-full" />
                        <div className="mt-3 flex gap-2">
                          <Skeleton className="h-6 w-16" />
                          <Skeleton className="h-6 w-20" />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <VirtualizedList items={rawList} pinned={pinned} acknowledged={acknowledged} onPin={handlePin} onAck={handleAck} />
              )}
            </div>
          </div>
        )}
      </section>

      {/* Export FAB */}
      {!error && (
          <aside className="fixed bottom-5 right-5 z-40 flex gap-2">
            <Button variant="secondary" onClick={handleDownloadJson} disabled={!data?.json_path}>
              <FileJson className="mr-2" /> Download JSON
            </Button>
            <Button variant="default" onClick={handleExportClips} disabled={exporting}>
              <Download className="mr-2" /> {exporting ? "Preparing ZIP…" : "Export clips"}
            </Button>
          </aside>
      )}
    </main>
  );
};

export default ResultsPage;
