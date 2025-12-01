import React, { useCallback, useMemo, useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { UploadCloud, Info, ExternalLink } from "lucide-react";
import { SEOHead } from "@/components/SEO";
import { useUpload, VideoMetadata } from "@/context/UploadContext";
import { cn } from "@/lib/utils";
import PromptChipsInput from "@/components/PromptChipsInput";
import { VideoRangeSelector } from "@/components/VideoRangeSelector";
import { formatHMS } from "@/lib/time";
import UrlIngestForm from "@/components/UrlIngestForm";
import { handleUrlIngestError } from "@/lib/urlIngest";

const MAX_BYTES = 2 * 1024 * 1024 * 1024; // 2GB
const MAX_SECONDS = 2 * 60 * 60; // 2 hours
const ACCEPTED_EXT = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"];

const humanFileSize = (bytes: number) => {
  const thresh = 1024;
  if (Math.abs(bytes) < thresh) return bytes + " B";
  const units = ["KB", "MB", "GB", "TB"];
  let u = -1;
  do {
    bytes /= thresh;
    ++u;
  } while (Math.abs(bytes) >= thresh && u < units.length - 1);
  return `${bytes.toFixed(1)} ${units[u]}`;
};

const timecode = (sec: number) => {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h > 0) return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

const getExtension = (name: string) => name.slice(name.lastIndexOf(".")).toLowerCase();

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const { setFileWithMetadata, file, metadata, analysisRange, setAnalysisRange, prompts, model, mode } = useUpload();
  const [dragOver, setDragOver] = useState(false);
  const [consent, setConsent] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [urlIngestData, setUrlIngestData] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onSelectFile = useCallback(async (f: File) => {
    const extOk = ACCEPTED_EXT.includes(getExtension(f.name));
    if (!extOk) {
      toast.error("Unsupported format", {
        description: `Allowed: ${ACCEPTED_EXT.join(", ")}`,
      });
      return;
    }

    if (f.size > MAX_BYTES) {
      toast.error("File too large", { description: "Max 2GB" });
      return;
    }

    // Extract metadata via a temporary video element
    const objectUrl = URL.createObjectURL(f);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.src = objectUrl;
    video.muted = true;
    video.playsInline = true;

    const metaPromise = new Promise<VideoMetadata>((resolve, reject) => {
      const cleanup = () => URL.revokeObjectURL(objectUrl);
      const onLoaded = async () => {
        try {
          const width = video.videoWidth || 0;
          const height = video.videoHeight || 0;
          const duration = isFinite(video.duration) ? video.duration : 0;

          // Best-effort FPS estimation using rVFC if playback starts (may fail; then we use "—")
          let fps: number | null = null;

          try {
            let frames = 0;
            const start = performance.now();
            const maxWindowMs = 600; // ~0.6s sampling
            const handle = (now: number) => {
              frames++;
              if (now - start < maxWindowMs) {
                (video as any).requestVideoFrameCallback?.(handle);
              }
            };
            (video as any).requestVideoFrameCallback?.(handle);
            await video.play().catch(() => {});
            await new Promise((r) => setTimeout(r, maxWindowMs));
            video.pause();
            const elapsed = performance.now() - start;
            if (frames > 0 && elapsed > 0) fps = Math.round((frames / elapsed) * 1000);
          } catch (_) {}

          const meta: VideoMetadata = {
            duration,
            width,
            height,
            fps: fps ?? null,
            sizeBytes: f.size,
            resolution: width && height ? `${width}×${height}` : "—",
          };

          if (duration > MAX_SECONDS) {
            toast.error("Video too long", { description: "Max 2 hours" });
            cleanup();
            reject(new Error("Too long"));
            return;
          }

          resolve(meta);
          cleanup();
        } catch (e) {
          reject(e);
        }
      };

      const onError = () => {
        URL.revokeObjectURL(objectUrl);
        reject(new Error("Failed to read video metadata"));
      };

      video.addEventListener("loadedmetadata", onLoaded, { once: true });
      video.addEventListener("error", onError, { once: true });
    });

    try {
      const meta = await metaPromise;
      setFileWithMetadata(f, meta);
      toast.success("Video added", { description: `${f.name} (${humanFileSize(f.size)})` });
    } catch (e) {
      // already handled by toasts
    }
  }, [setFileWithMetadata]);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) onSelectFile(f);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onSelectFile(f);
  };

  // Update analysis range when video duration changes
  useEffect(() => {
    if (metadata?.duration && !urlIngestData) {
      const duration = metadata.duration;
      const defaultEnd = Math.min(30, duration); // Default to 30s or full duration
      setAnalysisRange([0, defaultEnd]);
    } else if (urlIngestData?.duration_s) {
      const duration = urlIngestData.duration_s;
      const defaultEnd = Math.min(30, duration); // Default to 30s or full duration
      setAnalysisRange([0, defaultEnd]);
    }
  }, [metadata?.duration, urlIngestData]);

  const canContinue = !!file && !!metadata && consent;

  // URL ingestion handlers
  const handleUrlIngestComplete = useCallback((data: any) => {
    setUrlIngestData(data);
    // Create a mock file and metadata for the URL ingestion
    const mockMetadata: VideoMetadata = {
      duration: data.duration,
      width: 1920, // Default values
      height: 1080,
      fps: 30,
      sizeBytes: 0,
      resolution: "1920×1080"
    };
    setFileWithMetadata(new File([], data.title, { type: "video/mp4" }), mockMetadata);
  }, [setFileWithMetadata]);

  const handleUrlIngestError = useCallback((error: string) => {
    setUrlIngestData(null);
    toast.error(error);
  }, []);

  const handleAnalyzeFromUrl = useCallback(async () => {
    if (!urlIngestData || !prompts.length) return;
    setIsAnalyzing(true);
    try {
      const [startS, endS] = analysisRange;
      const body = {
        media_id: urlIngestData.media_id,
        prompts,
        model: model || "clip",
        analysisWindow: {
          start: formatHMS(startS),
          end: formatHMS(endS),
          offsetSeconds: startS
        }
      };
      const resp = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err?.detail || `HTTP ${resp.status}`);
      }
      const jobId = urlIngestData.media_id;
      // Navigate to progress page instead of waiting directly
      navigate(`/progress?jobId=${jobId}`);
    } catch (error) {
      console.error("Analysis error:", error);
      const errorMessage = error instanceof Error ? error.message : "Analysis failed";
      toast.error(errorMessage);
    } finally {
      setIsAnalyzing(false);
    }
  }, [urlIngestData, prompts, model, analysisRange, navigate]);

  const gradientStyle = useMemo(() => ({
    background: "linear-gradient(135deg, hsl(var(--gradient-upload-from)) 0%, hsl(var(--gradient-upload-to)) 100%)",
  }), []);

  return (
    <div className="min-h-screen" style={gradientStyle}>
      <SEOHead
        title="Upload CCTV Footage | Surveillance AI"
        description="Upload CCTV footage securely for AI analysis. Drag-and-drop with instant metadata and consent."
        canonical={typeof window !== "undefined" ? window.location.origin + "/upload" : "/upload"}
      />

      <header className="container pt-8 pb-4">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold tracking-tight">Surveillance AI</div>
          <div className="text-sm text-muted-foreground">M1 • Upload</div>
        </div>
      </header>

      <main className="container pb-12">
        <h1 className="sr-only">Upload CCTV Footage</h1>
        <Card className={cn("mx-auto max-w-3xl rounded-2xl shadow-lg border bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/70")}> 
          <CardHeader>
            <CardTitle className="text-2xl">Select your footage</CardTitle>
            <CardDescription>Upload a local file or fetch from YouTube URL for analysis.</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="upload" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  <UploadCloud className="h-4 w-4" />
                  Upload File
                </TabsTrigger>
                <TabsTrigger value="url" className="flex items-center gap-2">
                  <ExternalLink className="h-4 w-4" />
                  From URL
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="upload" className="mt-6">
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={onDrop}
                  className={cn(
                    "relative flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-xl p-8 transition-colors", 
                    dragOver ? "border-primary bg-muted/50" : "border-border"
                  )}
                >
                  <UploadCloud className="h-8 w-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground text-center">
                    Drag & drop CCTV footage here, or click to browse.
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_EXT.join(",")}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    onChange={onInputChange}
                  />
                  <div className="text-xs text-muted-foreground mt-2">
                    Accepted: {ACCEPTED_EXT.join(", ")}
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="url" className="mt-6">
                <UrlIngestForm 
                  onIngestComplete={handleUrlIngestComplete}
                  onError={handleUrlIngestError}
                  onRangeChange={(r) => setAnalysisRange(r)}
                />
              </TabsContent>
            </Tabs>

            {file && metadata && (
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg border bg-background p-4">
                  <div className="text-sm font-medium">File</div>
                  <div className="text-sm text-muted-foreground truncate">{file.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">{humanFileSize(file.size)}</div>
                </div>
                <div className="rounded-lg border bg-background p-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <div className="font-medium">Duration</div>
                    <div className="text-muted-foreground">{timecode(metadata.duration)}</div>
                  </div>
                  <div>
                    <div className="font-medium">Resolution</div>
                    <div className="text-muted-foreground">{metadata.resolution}</div>
                  </div>
                  <div>
                    <div className="font-medium">FPS</div>
                    <div className="text-muted-foreground">{metadata.fps ?? "—"}</div>
                  </div>
                </div>
              </div>
            )}

            {file && metadata && !urlIngestData && (
              <div className="mt-6">
                <VideoRangeSelector
                  duration={metadata.duration}
                  value={analysisRange}
                  onChange={setAnalysisRange}
                  step={1}
                />
              </div>
            )}

            {/* Analysis window for URL uploads is rendered inside UrlIngestForm after fetch */}

            <div className="mt-6">
              <PromptChipsInput
                label="What do you want to detect?"
                placeholder="e.g., man in red shirt, fire, black SUV"
                helper="Use simple phrases separated by commas"
                disabled={!file && !urlIngestData}
              />
            </div>

            <div className="mt-6 flex items-start gap-3">
              <Checkbox id="consent" checked={consent} onCheckedChange={(v) => setConsent(Boolean(v))} />
              <div className="grid gap-1.5 text-sm">
                <Label htmlFor="consent" className="font-medium">I confirm this video complies with local surveillance laws and contains no prohibited content.</Label>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button aria-label="consent info" className="inline-flex items-center">
                        <Info className="h-4 w-4" />
                      </button>
</TooltipTrigger>
                  <TooltipContent>
                    We don’t store your videos. Processing is ephemeral and runs on your infrastructure. Metadata is used only to perform analysis.
                  </TooltipContent>
                  </Tooltip>
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              {urlIngestData ? (
                <Button 
                  size="lg" 
                  disabled={!canContinue || isAnalyzing} 
                  onClick={handleAnalyzeFromUrl}
                >
                  {isAnalyzing ? "Analyzing..." : "Analyze Video"}
                </Button>
              ) : (
                <Button size="lg" disabled={!canContinue} onClick={() => navigate("/configure")}>
                  Continue
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Upload;
