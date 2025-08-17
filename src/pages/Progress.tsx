import React, { useEffect, useMemo, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { SEOHead } from "@/components/SEO";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress as ProgressBar } from "@/components/ui/progress";
import { useUpload, AnalyzeMode } from "@/context/UploadContext";
import { Brain, Zap, Move, Link as LinkIcon, PersonStanding, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import api from "@/lib/api";

const MODE_META: Record<AnalyzeMode, { label: string; icon: React.ComponentType<any>; factor: number }> = {
  FullScan: { label: "FullScan", icon: Brain, factor: 1.5 },
  FrameSkip: { label: "FrameSkip", icon: Zap, factor: 0.5 },
  MotionFilter: { label: "MotionFilter", icon: Move, factor: 0.7 },
  TrackThenMatch: { label: "TrackThenMatch", icon: LinkIcon, factor: 1.0 },
  ActivityDetect: { label: "ActivityDetect", icon: PersonStanding, factor: 1.2 },
};

const humanFileSize = (bytes: number) => {
  const thresh = 1024;
  if (Math.abs(bytes) < thresh) return bytes + " B";
  const units = ["KB", "MB", "GB", "TB"]; let u = -1;
  do { bytes /= thresh; ++u; } while (Math.abs(bytes) >= thresh && u < units.length - 1);
  return `${bytes.toFixed(1)} ${units[u]}`;
};

const fmtEta = (sec: number | null | undefined) => {
  const s = Math.max(0, Math.floor(sec || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
};

const ProgressPage: React.FC = () => {
  const navigate = useNavigate();
  const [search] = useSearchParams();
  const { file, metadata, prompts, model, mode } = useUpload();

  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("Contacting server…");
  const [eta, setEta] = useState<number | null>(null);
  const [stall, setStall] = useState(false);
  const [health, setHealth] = useState<{ device?: string; gpu?: string; modelCache?: string } | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [hadError, setHadError] = useState<string | null>(null);

  // Gradient background reused from M1 tokens
  const gradientStyle = useMemo(() => ({
    background: "linear-gradient(135deg, hsl(var(--gradient-upload-from)) 0%, hsl(var(--gradient-upload-to)) 100%)",
  }), []);

  // Guardrail: allow page to load with jobId even without file/metadata.
  useEffect(() => {
    const jobId = search.get("jobId");
    if (!jobId && (!file || !metadata)) {
      import("sonner").then(({ toast }) => {
        toast.error("No job in progress", { description: "Redirecting to Upload…" });
      });
      const t = setTimeout(() => navigate("/upload"), 1200);
      return () => clearTimeout(t);
    }
  }, [file, metadata, navigate, search]);

  // Compute optimistic ETA from mode and duration
  const optimisticEta = useMemo(() => {
    if (!metadata || !mode) return null;
    const factor = MODE_META[mode].factor;
    return Math.round((metadata.duration || 0) * factor);
  }, [metadata, mode]);

  // Stall banner timer (>45s) is managed and reset when progress advances
  const lastProgressRef = useRef(0);
  const stallTimerRef = useRef<number | null>(null);
  useEffect(() => {
    if (stallTimerRef.current) window.clearTimeout(stallTimerRef.current);
    stallTimerRef.current = window.setTimeout(() => setStall(true), 45000);
    return () => { if (stallTimerRef.current) window.clearTimeout(stallTimerRef.current); };
  }, [progress]);
  // Real polling using centralized API
  useEffect(() => {
    const jobId = search.get("jobId");
    if (!jobId) {
      setStatusText("Missing jobId");
      setHadError("Missing jobId");
      return;
    }
    let stopped = false;
    const poll = async () => {
      try {
        const slow = localStorage.getItem("dev.slowMode") === "1";
        if (slow) await new Promise((r) => setTimeout(r, 2000 + Math.floor(Math.random() * 2000)));
        const data = await api.getStatus(jobId);
        if (typeof data.progress === "number") {
          setProgress(Math.min(100, Math.max(0, data.progress)));
          lastProgressRef.current = data.progress;
          setStall(false); // progress moved; clear stall
        }
        if (typeof data.etaSeconds === "number") setEta(data.etaSeconds ?? null);
        if (data.status) setStatusText(data.status);
        if (data.status === "complete" && !stopped) {
          stopped = true;
          import("sonner").then(({ toast }) => toast.success("Analysis complete", { description: "Opening results…" }));
          setTimeout(() => navigate(`/results?jobId=${encodeURIComponent(jobId)}`), 500);
          return;
        }
        if (data.status === "error") {
          setHadError(data.message || "Server reported an error");
          import("sonner").then(({ toast }) => toast.error("Analysis failed", { description: data.message || "Please try again" }));
          return;
        }
        if (!stopped) setTimeout(poll, 900);
      } catch (e: any) {
        if (!stopped) setTimeout(poll, 1500);
      }
    };
    poll();
    return () => { stopped = true; };
  }, [search, navigate]);

  const EtaDisplay = fmtEta(eta ?? optimisticEta ?? 0);

  return (
    <div className="min-h-screen" style={gradientStyle}>
      <SEOHead
        title="Analyzing – Surveillance AI"
        description="Real-time analysis progress for your surveillance video."
        canonical={typeof window !== "undefined" ? window.location.origin + "/progress" : "/progress"}
      />

      <header className="container pt-8 pb-4">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold tracking-tight">Surveillance AI</div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>M3 • Analyzing</span>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs"
                  onMouseEnter={async () => {
                    if (health || healthLoading) return;
                    try {
                      setHealthLoading(true);
                      const h = await api.getHealth();
                      setHealth({ device: h.device, gpu: h.gpu, modelCache: h.modelCache });
                    } finally {
                      setHealthLoading(false);
                    }
                  }}
                  aria-label="Environment health"
                >
                  <Info className="h-3.5 w-3.5" /> Env
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <div className="text-xs">
                  <div><span className="text-muted-foreground">Device:</span> {health?.device ?? (healthLoading ? "…" : "—")}</div>
                  <div><span className="text-muted-foreground">GPU:</span> {health?.gpu ?? (healthLoading ? "…" : "—")}</div>
                  <div><span className="text-muted-foreground">Model cache:</span> {health?.modelCache ?? (healthLoading ? "…" : "—")}</div>
                </div>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </header>

      <main className="container pb-12">
        {stall && (
          <div className="mb-4 rounded-md border bg-muted/40 p-3 text-sm">Still processing… you can keep this tab open.</div>
        )}
        <h1 className="sr-only">Analyzing – Surveillance AI</h1>

        <div className="mx-auto max-w-4xl grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: spinner and progress */}
          <section className="lg:col-span-3 flex flex-col items-center justify-center rounded-2xl border bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/70 p-8 text-center shadow-lg">
            <div className="h-12 w-12 rounded-full border-4 border-muted border-t-primary animate-spin" aria-label="Loading" />
            <div className="mt-4 text-sm text-muted-foreground">{statusText}</div>
            <div className="mt-6 w-full">
              <ProgressBar value={progress} />
              <div className="mt-2 text-xs text-muted-foreground">Estimated Time • {EtaDisplay}</div>
            </div>
            <div className="mt-8">
              <Button variant="secondary" onClick={() => navigate("/configure")}>Back to Configure</Button>
            </div>
          </section>

          {/* Right: summary */}
          <section className="lg:col-span-2">
            <Card className="rounded-2xl shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg">Summary</CardTitle>
                <CardDescription>Submitted analysis settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                {/* File info */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs uppercase text-muted-foreground">File</div>
                    <div className="truncate" title={file?.name}>{file?.name ?? "—"}</div>
                    {file && <div className="text-muted-foreground text-xs">{humanFileSize(file.size)}</div>}
                  </div>
                  <div>
                    <div className="text-xs uppercase text-muted-foreground">Duration</div>
                    <div>{metadata ? fmtEta(metadata.duration) : "—"}</div>
                    <div className="text-xs text-muted-foreground">{metadata?.resolution ?? "—"}</div>
                  </div>
                </div>

                {/* Prompts */}
                <div>
                  <div className="text-xs uppercase text-muted-foreground mb-1">Prompts</div>
                  <div className="flex flex-wrap gap-2">
                    {(prompts || []).length > 0 ? (
                      (prompts || []).map((p, i) => (
                        <Badge key={`${p}-${i}`} variant="secondary">{p}</Badge>
                      ))
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </div>
                </div>

                {/* Mode & Model */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2">
                    {mode ? React.createElement(MODE_META[mode].icon, { className: "h-4 w-4" }) : null}
                    <div>
                      <div className="text-xs uppercase text-muted-foreground">Mode</div>
                      <div>{mode ? MODE_META[mode].label : "—"}</div>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase text-muted-foreground">Model</div>
                    <div className="capitalize">{model || "clip"}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>
      </main>
    </div>
  );
};

export default ProgressPage;
