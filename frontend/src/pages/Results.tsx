import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { SEOHead } from "@/components/SEO";
import { useUpload } from "@/context/UploadContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { Download, FileJson, Filter, Pin, PinOff, CheckCircle2, PlayCircle, Settings, BarChart3, X, ExternalLink } from "lucide-react";
import PromptChipsInput from "@/components/PromptChipsInput";
import { API_BASE } from "@/lib/api";
import { formatHMS } from "@/lib/time";
import { useVirtualizer } from "@tanstack/react-virtual";
import LazyVideo from "@/components/LazyVideo";
import { VirtualizedList } from "@/components/VirtualizedList";
import VirtualPreview from "@/components/VirtualPreview";
import { parseHMS } from "@/lib/time";
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

// DIAGNOSTIC MODE TYPES - For engine testing and performance analysis
type DiagnosticMode = {
  enabled: boolean;
  thresholds: Record<string, number>; // label -> threshold value
  falsePositives: Set<string>; // clip IDs marked as false positives
  promptPreview: string; // shows how prompts get parsed
};

type MergedPreview = {
  label: string;
  start: string;
  end: string;
  duration: number;
  confidence_peak: number;
  url: string;
};

export type AnalysisResponse = {
  status: string;
  video_id: string;
  results: ResultEntry[];
  alert_summary?: any; // Backend may return nested objects (e.g., priorities, categories)
  analysis_timestamp?: string;
  json_path?: string;
  prompts?: string[]; // DIAGNOSTIC MODE: Original prompts used for analysis
  analysisWindow?: { // PORTION ANALYSIS: Analysis window information
    start: string;
    end: string;
    offsetSeconds: number;
  };
  previewSets?: {
    merged?: Array<{
      label: string;
      start: string;
      end: string;
      duration: number;
      confidence_peak: number;
      url: string;
    }>;
  };
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
  const { jobId, prompts } = useUpload();
  const [searchParams, setSearchParams] = useSearchParams();
  const jid = searchParams.get("jobId") || jobId || "";

  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Runs history state
  type RunSummary = {
    jobId: string;
    prompts: string[];
    analysisWindow?: AnalysisResponse["analysisWindow"];
    detections?: number;
    createdAt: string;
    status: "pending" | "processing" | "complete" | "error";
  };
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const resultsCache = useRef<Map<string, AnalysisResponse>>(new Map());

  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [pinned, setPinned] = useState<Set<number>>(new Set());
  const [acknowledged, setAcknowledged] = useState<Set<number>>(new Set());

  const [exporting, setExporting] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [configOpen, setConfigOpen] = useState(false);
  const [reAnalyzing, setReAnalyzing] = useState(false);
  const [cacheOk, setCacheOk] = useState<boolean | null>(null);
  const initRef = useRef(false);
  const { toast } = useToast();

  // Re-run UI state - local prompts for new queries (separate from UploadContext)
  const [newQueryPrompts, setNewQueryPrompts] = useState<string[]>([]);
  const [newQueryInput, setNewQueryInput] = useState("");
  const [storedMediaId, setStoredMediaId] = useState<string | null>(null);

  // DIAGNOSTIC MODE STATE - For engine testing and performance analysis
  const [diagnosticMode, setDiagnosticMode] = useState<DiagnosticMode>({
    enabled: false,
    thresholds: {},
    falsePositives: new Set(),
    promptPreview: ""
  });
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

  // Restore runs from localStorage once
  useEffect(() => {
    try {
      const raw = localStorage.getItem("results.runs");
      if (raw) {
        const arr = JSON.parse(raw) as RunSummary[];
        setRuns(arr);
      }
    } catch {}
  }, []);

  // Persist runs summaries
  useEffect(() => {
    try { localStorage.setItem("results.runs", JSON.stringify(runs.slice(0, 5))); } catch {}
  }, [runs]);

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
          // Store media_id for re-runs
          if ((json as any)?.media?.media_id) {
            setStoredMediaId((json as any).media.media_id);
          }
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

  // Optional: verify cached media availability via HEAD/Range request
  useEffect(() => {
    const check = async () => {
      try {
        if (!data?.media?.original_url) { setCacheOk(null); return; }
        const url = (data.media as any).original_url as string;
        const res = await fetch(url, { method: 'GET', headers: { 'Range': 'bytes=0-0' } });
        setCacheOk(res.ok);
      } catch {
        setCacheOk(false);
      }
    };
    check();
  }, [data?.media?.original_url]);

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

  // Extract all unique labels from results for dynamic filtering
  const availableLabels = useMemo(() => {
    if (!data?.results) return [];
    const allLabels = new Set<string>();
    data.results.forEach((r) => {
      r.labels.forEach((label) => allLabels.add(label));
    });
    return Array.from(allLabels).sort();
  }, [data?.results]);

  const filteredResults = useMemo(() => {
    if (!data?.results) return [] as ResultEntry[];
    if (activeFilters.length === 0) return data.results;
    return data.results.filter((r) => {
      const text = r.labels.join(" ").toLowerCase();
      return activeFilters.some((filter) => {
        // Check if filter is a category pattern
        const pats = CATEGORY_PATTERNS[filter];
        if (pats) {
          return pats.some((re) => re.test(text));
        }
        // Otherwise, treat as exact label match
        return r.labels.some((label) => label.toLowerCase() === filter.toLowerCase());
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

// Filter merged previews based on active filters
const filteredMergedPreviews = useMemo(() => {
  const mergedPreviews = data?.previewSets?.merged;
  if (!mergedPreviews || mergedPreviews.length === 0) return [];
  
  // If no filters active, return all merged previews
  if (activeFilters.length === 0) return mergedPreviews;
  
  // Filter merged previews based on active filters (OR logic - match any filter)
  return mergedPreviews.filter((merged) => {
    const labelText = merged.label.toLowerCase();
    
    return activeFilters.some((filter) => {
      // Check if filter is a category pattern
      const pats = CATEGORY_PATTERNS[filter];
      if (pats) {
        // Category filter - check if merged label matches any pattern
        return pats.some((re) => re.test(labelText));
      }
      // Otherwise, treat as exact label match
      return labelText === filter.toLowerCase();
    });
  });
}, [data?.previewSets?.merged, activeFilters]);

// Build timeline items - prioritize merged previews if available
const timelineItems = useMemo(() => {
  // If filtered merged previews exist, use them for timeline markers (one per merged clip)
  if (filteredMergedPreviews && filteredMergedPreviews.length > 0) {
    // Create markers from filtered merged previews
    const mergedMarkers = filteredMergedPreviews.map((merged, idx) => {
      // Find the first individual detection that falls within this merged preview
      const startSeconds = parseHMS(merged.start);
      const endSeconds = parseHMS(merged.end);
      
      // Find matching individual detection (closest to start of merged clip)
      let matchingDetection: ResultEntry | null = null;
      let matchingIndex = -1;
      
      if (data?.results) {
        for (let i = 0; i < data.results.length; i++) {
          const det = data.results[i];
          const detSeconds = toSeconds(det.timestamp);
          // Check if detection falls within merged preview time range
          if (detSeconds >= startSeconds - 1 && detSeconds <= endSeconds + 1) {
            // Check if labels match
            if (det.labels.includes(merged.label)) {
              matchingDetection = det;
              matchingIndex = i;
              break; // Use first match
            }
          }
        }
      }
      
      // Create a synthetic result entry for the merged preview
      const syntheticResult: ResultEntry = matchingDetection || {
        timestamp: merged.start,
        labels: [merged.label],
        confidence: merged.confidence_peak,
        preview_clip: merged.url || `virtual_preview_${merged.start.replace(/:/g, '_')}`,
      };
      
      return {
        type: "marker" as const,
        index: matchingIndex >= 0 ? matchingIndex : idx,
        r: syntheticResult,
        merged: true, // Flag to indicate this is from merged preview
        mergedData: merged, // Store original merged data
      };
    });
    
    // Apply clustering if too many markers
    const maxMarkers = Math.max(30, Math.round(120 * zoom));
    if (mergedMarkers.length <= maxMarkers) {
      return mergedMarkers;
    }
    
    // Cluster merged markers if needed
    const clusterSize = Math.ceil(mergedMarkers.length / maxMarkers);
    const clusters: Array<{ type: "cluster"; start: number; end: number; count: number }> = [];
    for (let s = 0; s < mergedMarkers.length; s += clusterSize) {
      const e = Math.min(mergedMarkers.length - 1, s + clusterSize - 1);
      clusters.push({ type: "cluster", start: s, end: e, count: e - s + 1 });
    }
    return clusters;
  }
  
  // Fallback to individual detections if no merged previews
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
}, [rawList, zoom, filteredMergedPreviews, data?.results]);

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

  // Helper to upsert a run summary
  const upsertRun = useCallback((partial: Partial<RunSummary> & { jobId: string }) => {
    setRuns((prev) => {
      const idx = prev.findIndex((r) => r.jobId === partial.jobId);
      const next = [...prev];
      if (idx >= 0) next[idx] = { ...next[idx], ...partial } as RunSummary;
      else next.unshift({
        jobId: partial.jobId,
        prompts: partial.prompts || [],
        analysisWindow: partial.analysisWindow,
        detections: partial.detections,
        createdAt: new Date().toISOString(),
        status: partial.status || "pending",
      });
      return next.slice(0, 5);
    });
  }, []);

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

  // Export individual clip function
  const handleExportClip = async (mediaId: string, start: string, end: string, label: string) => {
    try {
      toast({ title: "Exporting clip", description: `Preparing ${label} clip...` });
      
      const response = await fetch('http://127.0.0.1:8000/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          media_id: mediaId,
          start: start,
          end: end,
          label: label,
          format: 'mp4'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Export failed (${response.status})`);
      }

      const exportData = await response.json();
      
      // Show success toast with download link
      toast({
        title: "Export ready",
        description: `Clip exported successfully (${(exportData.size_bytes / 1024 / 1024).toFixed(1)} MB)`,
        action: (
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              const a = document.createElement('a');
              a.href = exportData.url;
              a.download = `${label}_${start.replace(/:/g, '-')}_to_${end.replace(/:/g, '-')}.mp4`;
              a.rel = 'noopener';
              a.target = '_blank';
              document.body.appendChild(a);
              a.click();
              a.remove();
            }}
          >
            <Download className="w-4 h-4 mr-1" />
            Download
          </Button>
        )
      });

    } catch (error: any) {
      toast({
        title: "Export failed",
        description: error?.message || "Could not export clip. Please try again.",
        variant: "destructive"
      });
    }
  };

  // DIAGNOSTIC MODE FUNCTIONS - For engine testing and performance analysis
  const toggleDiagnosticMode = () => {
    setDiagnosticMode(prev => ({
      ...prev,
      enabled: !prev.enabled
    }));
  };

  const updateThreshold = (label: string, value: number) => {
    setDiagnosticMode(prev => ({
      ...prev,
      thresholds: { ...prev.thresholds, [label]: value }
    }));
  };

  const markFalsePositive = (clipId: string) => {
    setDiagnosticMode(prev => {
      const newFPs = new Set(prev.falsePositives);
      if (newFPs.has(clipId)) {
        newFPs.delete(clipId);
      } else {
        newFPs.add(clipId);
      }
      return { ...prev, falsePositives: newFPs };
    });
  };

  const resetDiagnosticMode = () => {
    setDiagnosticMode({
      enabled: false,
      thresholds: {},
      falsePositives: new Set(),
      promptPreview: ""
    });
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
            <Button variant="outline" onClick={() => setConfigOpen((v) => !v)}>{configOpen ? "Close" : "Configure"}</Button>
            <Button variant="secondary" onClick={() => navigate("/progress?jobId=" + encodeURIComponent(jid))}>
              <PlayCircle className="mr-2" /> Progress
            </Button>
          </div>
        </header>

        {/* Source meta row */}
        {data?.media && (
          <div className="mb-4 text-sm text-muted-foreground">
            {(() => {
              const mediaId = data.media as any;
              const isYouTube = (mediaId.media_id || "").startsWith("yt_");
              const sourceLabel = isYouTube ? "YouTube" : "Local";
              const dur = (data.media as any).duration_s;
              const durationText = typeof dur === "number" ? formatHMS(Math.max(0, Math.floor(dur))) : undefined;
              // Format label unknown in results; if we add later, read from data.media.format_label
              const parts = [sourceLabel, durationText].filter(Boolean);
              return <div>{parts.join(" • ")}</div>;
            })()}
            {/* Refetch CTA if cache missing and provenance available */}
            {cacheOk === false && (data as any)?.media?.provenance?.source_url && (
              <div className="mt-2">
                <Button size="sm" variant="outline" onClick={async () => {
                  try {
                    const sourceUrl = (data as any).media.provenance.source_url as string;
                    const body = { source: 'youtube', url: sourceUrl, action: 'fetch' } as any;
                    toast({ title: 'Restoring cache', description: 'Fetching video again…' });
                    const res = await fetch(`${API_BASE}/media/fetch`, {
                      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                    });
                    if (!res.ok) {
                      const err = await res.json().catch(() => ({}));
                      throw new Error(err?.detail || `HTTP ${res.status}`);
                    }
                    const json = await res.json();
                    // Update cache status and media original URL if provided
                    setCacheOk(true);
                    if (json?.file_url) {
                      setData((prev) => prev ? { ...prev, media: { ...(prev.media as any), original_url: json.file_url } as any } : prev);
                    }
                    toast({ title: 'Cache restored', description: 'You can analyze again now.' });
                  } catch (e: any) {
                    toast({ title: 'Refetch failed', description: e?.message || 'Unable to refetch video.', variant: 'destructive' });
                  }
                }}>Refetch video</Button>
              </div>
            )}
          </div>
        )}

        {/* Ask Another Question - Re-run UI */}
        {data && storedMediaId && (
          <Card className="mb-6 border-primary/20 bg-primary/5 animate-fade-in">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <PlayCircle className="h-5 w-5" />
                Ask another question on this video
              </CardTitle>
              <CardDescription>
                Search again using cached video data. No re-upload needed - this will be fast.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Prompt input with chips */}
                <div>
                  <Label className="text-sm font-medium mb-2 block">What do you want to detect?</Label>
                  <div className="min-h-[46px] w-full rounded-[var(--radius)] border bg-background px-2 py-2 flex flex-wrap items-center gap-2 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 shadow-sm">
                    {newQueryPrompts.map((p, i) => (
                      <Badge key={`${p}-${i}`} variant="secondary" className="h-7 gap-1">
                        <span>{p}</span>
                        <button
                          type="button"
                          aria-label={`Remove ${p}`}
                          className="ml-1 inline-flex items-center"
                          onClick={() => {
                            const next = [...newQueryPrompts];
                            next.splice(i, 1);
                            setNewQueryPrompts(next);
                          }}
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </Badge>
                    ))}
                    <Input
                      value={newQueryInput}
                      onChange={(e) => setNewQueryInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === ",") {
                          e.preventDefault();
                          const text = newQueryInput.trim();
                          if (text) {
                            const parts = text.split(",").map((p) => p.trim()).filter(Boolean);
                            if (parts.length > 0) {
                              const next = Array.from(new Set([...newQueryPrompts, ...parts]));
                              setNewQueryPrompts(next);
                              setNewQueryInput("");
                            }
                          }
                        } else if (e.key === "Backspace" && newQueryInput === "" && newQueryPrompts.length > 0) {
                          setNewQueryPrompts(newQueryPrompts.slice(0, -1));
                        }
                      }}
                      placeholder="e.g., person, car, fire"
                      className="flex-1 min-w-[160px] border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                      disabled={reAnalyzing}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">Use simple phrases separated by commas. Press Enter or comma to add.</p>
                </div>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    {reAnalyzing ? (
                      <span className="flex items-center gap-2">
                        <span className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        Running fast re-query on cached video…
                      </span>
                    ) : (
                      "This will reuse the cached video analysis for instant results."
                    )}
                  </div>
                  <Button
                    disabled={reAnalyzing || newQueryPrompts.length === 0}
                    onClick={async () => {
                      if (!storedMediaId || newQueryPrompts.length === 0) return;
                      try {
                        setReAnalyzing(true);
                        toast({ 
                          title: "Searching again", 
                          description: "Running fast re-query on cached video…",
                          duration: 2000
                        });
                        const body: any = {
                          media_id: storedMediaId,
                          prompts: newQueryPrompts,
                          model: "clip",
                        };
                        if (data.analysisWindow) body.analysisWindow = data.analysisWindow;
                        const res = await fetch(`${API_BASE}/analyze`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify(body),
                        });
                        if (!res.ok) {
                          const err = await res.json().catch(() => ({}));
                          throw new Error(err?.detail || `HTTP ${res.status}`);
                        }
                        const analyzeResponse = await res.json();
                        const newJobId = (
                          analyzeResponse.jobId ||
                          analyzeResponse.job_id ||
                          analyzeResponse.jid ||
                          analyzeResponse.video_id ||
                          (analyzeResponse.data && (analyzeResponse.data.jobId || analyzeResponse.data.jid)) ||
                          analyzeResponse.media_id
                        );
                        if (!newJobId) {
                          throw new Error("Analyze response did not include a jobId");
                        }
                        // Track new run as processing
                        upsertRun({ 
                          jobId: newJobId, 
                          prompts: newQueryPrompts, 
                          status: 'processing', 
                          analysisWindow: data?.analysisWindow 
                        });
                        // Reflect the new jobId in the URL immediately
                        try {
                          const next = new URLSearchParams(searchParams);
                          next.set("jobId", newJobId);
                          setSearchParams(next, { replace: true });
                        } catch {}

                        // Poll until complete (tolerate variant status values)
                        const isDone = (s: string | undefined) => {
                          if (!s) return false;
                          const v = s.toLowerCase();
                          return v === "complete" || v === "success" || v === "done" || v === "finished";
                        };
                        let attempts = 0;
                        let done = false;
                        while (!done && attempts < 120) {
                          attempts++;
                          try {
                            const status = await api.getStatus(newJobId);
                            if (isDone(status.status)) break;
                            if (status.status === "error") throw new Error("Analysis failed");
                          } catch (_) {
                            // ignore transient status errors and keep polling
                          }
                          await new Promise((r) => setTimeout(r, 1200));
                        }

                        // Final fetch
                        const latest = await api.getResults(newJobId);
                        resultsCache.current.set(newJobId, latest);
                        upsertRun({ 
                          jobId: newJobId, 
                          status: 'complete', 
                          detections: latest.results?.length || 0, 
                          analysisWindow: latest.analysisWindow 
                        });
                        setData(latest);
                        setSelectedIdx(latest.results?.length ? 0 : null);
                        // Clear the new query prompts after successful run
                        setNewQueryPrompts([]);
                        setNewQueryInput("");
                        toast({ 
                          title: "Re-query complete", 
                          description: `Found ${latest.results?.length ?? 0} detections with your new prompts.`,
                          duration: 3000
                        });
                      } catch (e: any) {
                        toast({ 
                          title: "Re-query failed", 
                          description: e?.message || "Please try again.", 
                          variant: "destructive" 
                        });
                      } finally {
                        setReAnalyzing(false);
                      }
                    }}
                  >
                    {reAnalyzing ? (
                      <>
                        <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        Searching…
                      </>
                    ) : (
                      "Search Again"
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Runs panel */}
        <div className="mb-6">
          {runs.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Runs</CardTitle>
                <CardDescription>Switch between analyses without leaving the page.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {runs.map((r) => {
                    const isActive = r.jobId === jid;
                    return (
                      <div key={r.jobId} className={`flex items-center justify-between rounded border p-2 ${isActive ? 'bg-accent/30' : 'bg-background'}`}>
                        <div className="flex items-center gap-3">
                          <Badge variant={r.status === 'complete' ? 'secondary' : r.status === 'error' ? 'destructive' : 'outline'}>
                            {r.status}
                          </Badge>
                          <div className="text-sm">
                            <div className="font-medium truncate max-w-[40ch]">{r.prompts?.join(", ") || "(no prompts)"}</div>
                            <div className="text-xs text-muted-foreground">
                              {new Date(r.createdAt).toLocaleString()} • {typeof r.detections === 'number' ? `${r.detections} detections` : '—'}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {!isActive && (
                            <Button size="sm" variant="outline" onClick={async () => {
                              const next = new URLSearchParams(searchParams);
                              next.set('jobId', r.jobId);
                              setSearchParams(next, { replace: true });
                              try {
                                const cached = resultsCache.current.get(r.jobId);
                                if (cached) { setData(cached); return; }
                                const res = await api.getResults(r.jobId);
                                resultsCache.current.set(r.jobId, res);
                                setData(res);
                              } catch (e:any) {
                                toast({ title: 'Load failed', description: e?.message || 'Could not load run.' , variant: 'destructive'});
                              }
                            }}>View</Button>
                          )}
                          {isActive && <Badge variant="outline">Active</Badge>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Configure inline - Analyze Again */}
        {configOpen && (
          <Card className="mb-6 animate-fade-in">
            <CardHeader>
              <CardTitle>Configure prompts</CardTitle>
              <CardDescription>Update prompts and re-run analysis using the same cached video.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <PromptChipsInput
                  label="What do you want to detect?"
                  placeholder="e.g., person, car, fire"
                  helper="Use simple phrases separated by commas"
                />
                <div className="flex justify-end">
                  <Button disabled={reAnalyzing || !prompts.length} onClick={async () => {
                    if (!data?.media?.media_id) return;
                    try {
                      setReAnalyzing(true);
                      toast({ title: "Re-running analysis", description: "Submitting job…" });
                      const body: any = {
                        media_id: (data.media as any).media_id,
                        prompts: prompts,
                      };
                      if (data.analysisWindow) body.analysisWindow = data.analysisWindow;
                      const res = await fetch(`${API_BASE}/analyze`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                      });
                      if (!res.ok) {
                        const err = await res.json().catch(() => ({}));
                        throw new Error(err?.detail || `HTTP ${res.status}`);
                      }
                      const analyzeResponse = await res.json();
                      const newJobId = (
                        analyzeResponse.jobId ||
                        analyzeResponse.job_id ||
                        analyzeResponse.jid ||
                        analyzeResponse.video_id ||
                        (analyzeResponse.data && (analyzeResponse.data.jobId || analyzeResponse.data.jid)) ||
                        analyzeResponse.media_id // final fallback (legacy)
                      );
                      if (!newJobId) {
                        throw new Error("Analyze response did not include a jobId");
                      }
                      // Track new run as processing
                      upsertRun({ jobId: newJobId, prompts: prompts || [], status: 'processing', analysisWindow: data?.analysisWindow });
                      // Reflect the new jobId in the URL immediately
                      try {
                        const next = new URLSearchParams(searchParams);
                        next.set("jobId", newJobId);
                        setSearchParams(next, { replace: true });
                      } catch {}

                      // Poll until complete (tolerate variant status values) and try fetching results periodically
                      const isDone = (s: string | undefined) => {
                        if (!s) return false;
                        const v = s.toLowerCase();
                        return v === "complete" || v === "success" || v === "done" || v === "finished";
                      };
                      let attempts = 0;
                      let done = false;
                      while (!done && attempts < 120) { // ~2 minutes max
                        attempts++;
                        try {
                          const status = await api.getStatus(newJobId);
                          if (isDone(status.status)) break;
                          if (status.status === "error") throw new Error("Analysis failed");
                        } catch (_) {
                          // ignore transient status errors and keep polling
                        }
                        await new Promise((r) => setTimeout(r, 1200));
                      }

                      // Final fetch
                      const latest = await api.getResults(newJobId);
                      resultsCache.current.set(newJobId, latest);
                      upsertRun({ jobId: newJobId, status: 'complete', detections: latest.results?.length || 0, analysisWindow: latest.analysisWindow });
                      setData(latest);
                      setSelectedIdx(latest.results?.length ? 0 : null);
                      toast({ title: "Analysis complete", description: `Found ${latest.results?.length ?? 0} detections.` });
                    } catch (e: any) {
                      toast({ title: "Re-run failed", description: e?.message || "Please try again.", variant: "destructive" });
                    } finally {
                      setReAnalyzing(false);
                    }
                  }}>{reAnalyzing ? "Analyzing…" : "Analyze Again"}</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

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
                            const { index, r, merged, mergedData } = item as any;
                            const isMerged = merged === true;
                            const displayTimestamp = isMerged && mergedData 
                              ? `${mergedData.start} - ${mergedData.end}` 
                              : r.timestamp;
                            const displayLabel = isMerged && mergedData 
                              ? mergedData.label 
                              : r.labels[0];
                            
                            return (
                              <Tooltip key={`${r.timestamp}-${index}-${idx}`}>
                                <TooltipTrigger asChild>
                                  <button
                                    ref={(el) => (markerRefs.current[index] = el)}
                                    className={`h-4 w-4 rounded-full border transition-transform hover:scale-110 motion-reduce:transform-none motion-reduce:transition-none ${
                                      index === selectedIdx ? "bg-primary ring-2 ring-primary/50" : "bg-secondary"
                                    } ${pinned.has(index) ? "border-primary" : ""} ${isMerged ? "ring-1 ring-blue-400" : ""}`}
                                    aria-label={`Go to ${displayTimestamp}`}
                                    onClick={() => setSelectedIdx(index)}
                                    title={isMerged ? `Merged clip: ${displayLabel} (${mergedData.duration.toFixed(1)}s)` : undefined}
                                  />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <div className="text-xs w-56">
                                    <div className="font-medium mb-2">
                                      {isMerged ? (
                                        <span>
                                          {displayLabel} <span className="text-muted-foreground">({mergedData.duration.toFixed(1)}s)</span>
                                        </span>
                                      ) : (
                                        displayTimestamp
                                      )}
                                    </div>
                                    {isMerged && mergedData && (
                                      <div className="text-xs text-muted-foreground mb-2">
                                        {displayTimestamp}
                                      </div>
                                    )}
                                    <div className="overflow-hidden rounded border bg-secondary">
                                      {(() => {
                                        // Check if this is a virtual preview (no actual clip file)
                                        const isVirtualPreview = r.preview_clip?.startsWith("virtual_preview_");
                                        const originalVideoUrl = (data?.media as any)?.original_url;
                                        
                                        // For merged previews, use the merged time range
                                        if (isMerged && mergedData && originalVideoUrl) {
                                          const clipStart = parseHMS(mergedData.start);
                                          const clipEnd = parseHMS(mergedData.end);
                                          const videoSrc = `${originalVideoUrl}#t=${clipStart},${clipEnd}`;
                                          
                                          return (
                                            <video
                                              src={videoSrc}
                                              muted
                                              playsInline
                                              preload="metadata"
                                              autoPlay
                                              loop
                                              className="w-full h-28 object-cover"
                                              onError={(e) => {
                                                const target = e.target as HTMLVideoElement;
                                                target.style.display = 'none';
                                              }}
                                            />
                                          );
                                        } else if (isVirtualPreview && originalVideoUrl) {
                                          // Use virtual preview with original video URL and timestamp
                                          const timestampSeconds = toSeconds(r.timestamp);
                                          const clipStart = Math.max(0, timestampSeconds - 1.5);
                                          const clipEnd = timestampSeconds + 1.5;
                                          const videoSrc = `${originalVideoUrl}#t=${clipStart},${clipEnd}`;
                                          
                                          return (
                                            <video
                                              src={videoSrc}
                                              muted
                                              playsInline
                                              preload="metadata"
                                              autoPlay
                                              loop
                                              className="w-full h-28 object-cover"
                                              onError={(e) => {
                                                // Fallback to static frame if video fails
                                                const target = e.target as HTMLVideoElement;
                                                target.style.display = 'none';
                                              }}
                                            />
                                          );
                                        } else {
                                          // Use actual preview clip file
                                          return (
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
                                          );
                                        }
                                      })()}
                                    </div>
                                    <div className="mt-2 flex flex-wrap gap-1">
                                      {isMerged && mergedData ? (
                                        <Badge variant="secondary">{mergedData.label}</Badge>
                                      ) : (
                                        r.labels.slice(0, 2).map((l, k) => (
                                          <Badge key={k} variant="secondary">{l}</Badge>
                                        ))
                                      )}
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
                            {(() => {
                              // Check if this is a virtual preview (no actual clip file)
                              const isVirtualPreview = selected.preview_clip?.startsWith("virtual_preview_");
                              const originalVideoUrl = (data?.media as any)?.original_url;
                              
                              if (isVirtualPreview && originalVideoUrl) {
                                // Use virtual preview with original video URL and timestamp
                                const timestampSeconds = toSeconds(selected.timestamp);
                                const clipStart = Math.max(0, timestampSeconds - 1.5);
                                const clipEnd = timestampSeconds + 1.5;
                                const videoSrc = `${originalVideoUrl}#t=${clipStart},${clipEnd}`;
                                
                                return (
                                  <video
                                    src={videoSrc}
                                    controls
                                    className="h-auto w-full"
                                    preload="metadata"
                                    playsInline
                                  />
                                );
                              } else {
                                // Use actual preview clip file
                                return (
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
                                );
                              }
                            })()}
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
                  <div className="space-y-4">
                    {/* Category Filters */}
                    <div>
                      <div className="text-sm font-medium mb-2">Categories</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.keys(CATEGORY_PATTERNS).map((key) => {
                          // Check if this category has any matches in current results
                          const hasMatches = data?.results?.some((r) => {
                            const text = r.labels.join(" ").toLowerCase();
                            const pats = CATEGORY_PATTERNS[key] || [];
                            return pats.some((re) => re.test(text));
                          });
                          
                          return (
                            <button
                              key={key}
                              onClick={() => handleToggleFilter(key)}
                              disabled={!hasMatches}
                              className={`inline-flex items-center rounded-full border px-3 py-1 text-sm transition-colors ${
                                activeFilters.includes(key)
                                  ? "bg-secondary text-secondary-foreground"
                                  : hasMatches
                                  ? "bg-background hover:bg-accent hover:text-accent-foreground"
                                  : "bg-background opacity-40 cursor-not-allowed"
                              }`}
                              title={hasMatches ? `Filter by ${key}` : `No ${key} found in results`}
                            >
                              {key}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Dynamic Label Filters */}
                    {availableLabels.length > 0 && (
                      <div>
                        <div className="text-sm font-medium mb-2">Labels ({availableLabels.length})</div>
                        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                          {availableLabels.map((label) => (
                            <button
                              key={label}
                              onClick={() => handleToggleFilter(label)}
                              className={`inline-flex items-center rounded-full border px-3 py-1 text-sm transition-colors ${
                                activeFilters.includes(label)
                                  ? "bg-primary text-primary-foreground"
                                  : "bg-background hover:bg-accent hover:text-accent-foreground"
                              }`}
                            >
                              {label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Filter Actions */}
                    <div className="flex gap-2 pt-2 border-t">
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

            {/* PORTION ANALYSIS: Analysis window information */}
            {data?.analysisWindow && (
              <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100">Analysis Window</h3>
                </div>
                <div className="text-sm text-blue-700 dark:text-blue-300">
                  <div>Analyzed segment: <span className="font-medium">{data.analysisWindow.start}</span> → <span className="font-medium">{data.analysisWindow.end}</span></div>
                  <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Timestamps in results are absolute (offset: {data.analysisWindow.offsetSeconds}s)
                  </div>
                </div>
              </div>
            )}

            {/* Merged previews (per-label continuous clips) - Virtual Preview Mode */}
            {filteredMergedPreviews && filteredMergedPreviews.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-lg font-semibold tracking-tight">
                  Merged previews (per label)
                  {activeFilters.length > 0 && (
                    <span className="text-sm text-muted-foreground ml-2">
                      ({filteredMergedPreviews.length} of {data?.previewSets?.merged?.length || 0} shown)
                    </span>
                  )}
                </h2>
                <div className="space-y-6">
                  {(() => {
                    const groups = new Map();
                    for (const m of filteredMergedPreviews) {
                      const arr: any[] = groups.get(m.label) || [];
                      arr.push(m);
                      groups.set(m.label, arr);
                    }
                    return Array.from(groups.entries()).map(([label, items]: [string, any[]]) => (
                      <Card key={label} className="animate-fade-in">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Badge variant="secondary">{label}</Badge>
                            <span className="text-sm text-muted-foreground">{items.length} clip{items.length>1?"s":""}</span>
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {items.map((it, idx) => {
                              // Determine video source
                              let videoSrc = "";
                              if (data?.media?.original_url) {
                                // Use original media URL for virtual previews
                                videoSrc = data.media.original_url;
                              } else {
                                // Fallback to server-generated URL if available
                                videoSrc = it.url || "";
                              }
                              
                              // Parse start and end times
                              const startSeconds = parseHMS(it.start);
                              const endSeconds = parseHMS(it.end);
                              
                              return (
                                <div key={`${label}-${idx}`} className="relative">
                                  <VirtualPreview
                                    src={videoSrc}
                                    start={startSeconds}
                                    end={endSeconds}
                                    label={label}
                                    className="w-full"
                                  />
                                  
                                  {/* Export and Diagnostic buttons overlay */}
                                  <div className="absolute top-2 right-2 z-10 flex gap-1">
                                    {/* Export clip button */}
                                    <Button
                                      size="sm"
                                      variant="secondary"
                                      onClick={() => handleExportClip(
                                        data?.media?.media_id || "",
                                        it.start,
                                        it.end,
                                        label
                                      )}
                                      className="bg-white/90 hover:bg-white text-gray-700 hover:text-gray-900"
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                    </Button>
                                    
                                    {/* DIAGNOSTIC MODE: False Positive Marking for Merged Clips */}
                                    {diagnosticMode.enabled && (
                                      <Button
                                        size="sm"
                                        variant={diagnosticMode.falsePositives.has(`${label}-${idx}`) ? "destructive" : "outline"}
                                        onClick={() => markFalsePositive(`${label}-${idx}`)}
                                        className="bg-white/90 hover:bg-white"
                                      >
                                        {diagnosticMode.falsePositives.has(`${label}-${idx}`) ? "FP" : "Mark FP"}
                                      </Button>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </CardContent>
                      </Card>
                    ));
                  })()}
                </div>
              </div>
            )}

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
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {rawList.map((item, index) => (
                    <Card
                      key={`${item.timestamp}-${index}`}
                      className={`relative transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
                        pinned.has(index) ? "ring-1 ring-primary/30" : ""
                      } ${acknowledged.has(index) ? "opacity-90" : ""}`}
                    >
                      <CardHeader className="space-y-1 pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">{item.timestamp}</CardTitle>
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant={pinned.has(index) ? "secondary" : "outline"}
                              onClick={() => handlePin(index)}
                              aria-pressed={pinned.has(index)}
                              aria-label={pinned.has(index) ? "Unpin alert" : "Pin alert"}
                            >
                              {pinned.has(index) ? <PinOff aria-hidden /> : <Pin aria-hidden />}
                            </Button>
                            <Button
                              size="sm"
                              variant={acknowledged.has(index) ? "secondary" : "outline"}
                              onClick={() => handleAck(index)}
                              aria-checked={acknowledged.has(index)}
                              role="checkbox"
                              aria-label={acknowledged.has(index) ? "Unacknowledge alert" : "Acknowledge alert"}
                            >
                              <CheckCircle2 aria-hidden />
                            </Button>
                          </div>
                        </div>
                        <CardDescription>Confidence: {Math.round(item.confidence * 100)}%</CardDescription>
                      </CardHeader>
                      <CardContent>
                        {pinned.has(index) && (
                          <Badge variant="secondary" className="absolute left-2 top-2 z-10">
                            Pinned
                          </Badge>
                        )}
                        {acknowledged.has(index) && (
                          <Badge variant="outline" className="absolute left-2 top-10 z-10">
                            ✓ Acknowledged
                          </Badge>
                        )}
                        <div className="overflow-hidden rounded-lg border relative">
                          <LazyVideo 
                            src={item.preview_clip} 
                            controls 
                            className="h-auto w-full rounded-lg" 
                            preload="metadata" 
                            playsInline 
                          />
                          {/* DIAGNOSTIC MODE: False Positive Marking */}
                          {diagnosticMode.enabled && (
                            <Button
                              size="sm"
                              variant={diagnosticMode.falsePositives.has(`${item.timestamp}-${index}`) ? "destructive" : "outline"}
                              onClick={() => markFalsePositive(`${item.timestamp}-${index}`)}
                              className="absolute top-2 right-2 z-10"
                            >
                              {diagnosticMode.falsePositives.has(`${item.timestamp}-${index}`) ? "FP" : "Mark FP"}
                            </Button>
                          )}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {item.labels.map((label, k) => (
                            <Badge key={k} variant="outline">
                              {label}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* DIAGNOSTIC MODE PANEL - For engine testing and performance analysis */}
      {diagnosticMode.enabled && (
        <div className="fixed top-4 right-4 w-96 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-50 max-h-[80vh] overflow-y-auto">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                🔧 Diagnostic Mode
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={resetDiagnosticMode}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Engine testing tools for performance analysis
            </p>
          </div>
          
          <div className="p-4 space-y-4">
            {/* Threshold Controls */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Threshold Controls</h4>
              <div className="space-y-2">
                {data?.results && Array.from(new Set(data.results.flatMap(r => r.labels))).map(label => (
                  <div key={label} className="flex items-center gap-2">
                    <label className="text-sm text-gray-700 dark:text-gray-300 w-20 truncate">
                      {label}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={diagnosticMode.thresholds[label] || 0.5}
                      onChange={(e) => updateThreshold(label, parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-xs text-gray-500 w-12">
                      {Math.round((diagnosticMode.thresholds[label] || 0.5) * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* False Positive Tracking */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                False Positives ({diagnosticMode.falsePositives.size})
              </h4>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Click clips below to mark as false positive
              </div>
            </div>

            {/* Prompt Analysis */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Prompt Analysis</h4>
              <div className="space-y-2">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Original prompts: {data?.prompts?.join(", ") || "N/A"}
                </div>
                <div className="text-sm">
                  <div className="text-gray-600 dark:text-gray-400 mb-1">Parsed as individual labels:</div>
                  <div className="flex flex-wrap gap-1">
                    {data?.results && Array.from(new Set(data.results.flatMap(r => r.labels))).map(label => (
                      <Badge key={label} variant="outline" className="text-xs">
                        {label}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="text-xs text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 p-2 rounded">
                  ⚠️ Multi-word prompts like "yellow flowers" may be split into separate labels
                </div>
              </div>
            </div>

            {/* Confidence Distribution */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Confidence Distribution</h4>
              <div className="space-y-1">
                {data?.results && (() => {
                  const confidences = data.results.map(r => r.confidence);
                  const buckets = [0, 0.2, 0.4, 0.6, 0.8, 1.0];
                  const distribution = buckets.slice(0, -1).map((min, i) => {
                    const max = buckets[i + 1];
                    const count = confidences.filter(c => c >= min && c < max).length;
                    return { range: `${Math.round(min * 100)}-${Math.round(max * 100)}%`, count, percentage: (count / confidences.length) * 100 };
                  });
                  
                  return distribution.map((bucket, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <div className="w-16 text-gray-600 dark:text-gray-400">{bucket.range}</div>
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${bucket.percentage}%` }}
                        />
                      </div>
                      <div className="w-8 text-gray-600 dark:text-gray-400">{bucket.count}</div>
                    </div>
                  ));
                })()}
              </div>
            </div>

            {/* Performance Metrics */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Performance Metrics</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded">
                  <div className="text-gray-600 dark:text-gray-400">Total Detections</div>
                  <div className="font-medium">{data?.results?.length || 0}</div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded">
                  <div className="text-gray-600 dark:text-gray-400">Avg Confidence</div>
                  <div className="font-medium">
                    {data?.results ? Math.round(data.results.reduce((acc, r) => acc + r.confidence, 0) / data.results.length * 100) : 0}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Export FAB */}
      {!error && (
          <aside className="fixed bottom-5 right-5 z-40 flex gap-2">
            {/* DIAGNOSTIC MODE TOGGLE - For engine testing and performance analysis */}
            <Button 
              variant={diagnosticMode.enabled ? "default" : "outline"} 
              onClick={toggleDiagnosticMode}
              className={diagnosticMode.enabled ? "bg-orange-600 hover:bg-orange-700" : ""}
            >
              <Settings className="mr-2" /> 
              {diagnosticMode.enabled ? "Diagnostic ON" : "Diagnostic"}
            </Button>
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
