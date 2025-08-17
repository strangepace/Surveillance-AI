import React from "react";
import { useParams, useNavigate, Link, useSearchParams } from "react-router-dom";
import { SEOHead } from "@/components/SEO";
import { useLiveStore } from "@/context/LiveStore";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Check, Download, Pin, PinOff, Share2, Volume2, VolumeX, Play, Pause } from "lucide-react";
import { Input } from "@/components/ui/input";
import LazyVideo from "@/components/LazyVideo";

const LiveReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { alerts, pin, ack, setNote, live, filters, setFilters } = useLiveStore();

  const [searchParams, setSearchParams] = useSearchParams();

  const alert = alerts.find((a) => a.alertId === id);
  const [note, setNoteState] = React.useState(alert?.note ?? "");
  const [playing, setPlaying] = React.useState(true);
  const [muted, setMuted] = React.useState(true);
  const [rate, setRate] = React.useState(1);
  const [exporting, setExporting] = React.useState(false);
  const [exportUrl, setExportUrl] = React.useState<string | null>(null);
  const [exportErr, setExportErr] = React.useState<string | null>(null);

  const effectiveCamera = React.useMemo(() => (filters.cameraId || alert?.cameraId || ""), [filters.cameraId, alert?.cameraId]);

  // Hydrate camera from URL; keep store in sync with back/forward
  React.useEffect(() => {
    const urlCam = searchParams.get("cameraId") ?? "";
    if (urlCam !== (filters.cameraId || "")) {
      setFilters({ cameraId: urlCam || null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // If no camera in store, derive from alert and sync URL
  React.useEffect(() => {
    if (!filters.cameraId && alert?.cameraId) {
      setFilters({ cameraId: alert.cameraId });
      const next = new URLSearchParams(searchParams);
      next.set("cameraId", alert.cameraId);
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alert?.cameraId, filters.cameraId]);

  React.useEffect(() => {
    setNoteState(alert?.note ?? "");
  }, [id]);

  // Related alerts: same camera, within ±120s
  const related = React.useMemo(() => {
    if (!alert) return [] as typeof alerts;
    return alerts.filter((a) => a.cameraId === alert.cameraId && Math.abs(a.tsUnix - alert.tsUnix) <= 120).slice(0, 12);
  }, [alerts, alert]);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
    } catch {}
  };

  if (!alert) {
    return (
      <main className="container mx-auto p-4 md:p-6">
        <SEOHead title="Alert not found – Live Review" />
        <Button variant="outline" onClick={() => navigate(-1)}><ArrowLeft className="h-4 w-4 mr-2" />Back</Button>
        <div className="mt-6 text-sm">Alert not found.</div>
      </main>
    );
  }

  return (
    <main className="container mx-auto p-4 md:p-6">
      <SEOHead title={`Review – ${alert.category} ${Math.round(alert.confidence * 100)}%`} description="Alert review with clip playback and details." />
      <header className="flex items-center gap-2">
        <Button variant="ghost" onClick={() => navigate(-1)}><ArrowLeft className="h-4 w-4 mr-2" />Back to Alerts</Button>
        <span className="text-xs opacity-70 ml-2">Camera: {effectiveCamera || "default"}</span>
        <Button size="sm" variant="outline" asChild>
          <Link to={`/live/alerts?cameraId=${encodeURIComponent(effectiveCamera || "")}&q=${encodeURIComponent(alert.alertId)}`}>View in Alerts</Link>
        </Button>
        <div className="ml-auto flex items-center gap-2">
          <Badge variant="secondary">{alert.category}</Badge>
          <span className="text-xs opacity-70">{Math.round(alert.confidence * 100)}%</span>
          <Button size="sm" variant="ghost" onClick={() => pin(alert.alertId)} aria-label={alert.pinned ? "Unpin" : "Pin"} aria-pressed={alert.pinned}>
            {alert.pinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => ack(alert.alertId)} aria-label="Acknowledge" role="checkbox" aria-checked={alert.acknowledged}>
            <Check className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={onCopy}><Share2 className="h-4 w-4" /></Button>
          {exportUrl ? (
            <Button size="sm" variant="outline" asChild>
              <a href={exportUrl} target="_blank" rel="noopener noreferrer"><Download className="h-4 w-4 mr-1" /> Open export</a>
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={async () => {
                try {
                  setExportErr(null);
                  setExporting(true);
                  const exportId = await live.export(alert.alertId);
                  const { url } = await live.pollExport(exportId);
                  setExportUrl(url || null);
                } catch (e: any) {
                  setExportErr(String(e?.message || e));
                } finally {
                  setExporting(false);
                }
              }}
              disabled={exporting}
              variant="default"
              aria-busy={exporting}
              aria-live="polite"
            >
              <Download className="h-4 w-4 mr-1" /> {exporting ? "Exporting…" : "Export clip"}
            </Button>
          )}
        </div>
          {exportErr && <span className="text-xs text-destructive ml-2">{exportErr}</span>}
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6 mt-4">
        {/* Player */}
        <section className="lg:col-span-8">
          <Card>
            <CardContent className="p-0">
              <div className="relative bg-muted rounded-md overflow-hidden">
                {alert.clipUrl ? (
                  <VideoWithVisibility
                    src={alert.clipUrl}
                    poster={alert.thumbnailUrl}
                    muted={muted}
                    playing={playing}
                    onPlayChange={setPlaying}
                  />
                ) : (
                  <div className="aspect-video flex items-center justify-center text-sm text-muted-foreground">No clip available</div>
                )}
                {/* Minimal overlay controls */}
                <div className="absolute bottom-3 left-3 flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setPlaying((v) => !v)} aria-pressed={playing} aria-label={playing ? "Pause" : "Play"}>
                    {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => setMuted((v) => !v)} aria-pressed={muted} aria-label={muted ? "Unmute" : "Mute"}>
                    {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                  </Button>
                  <Button size="sm" variant="outline" asChild>
                    <a href={alert.clipUrl || "#"} download={Boolean(alert.clipUrl)} aria-disabled={!alert.clipUrl} onClick={(e) => { if (!alert.clipUrl) e.preventDefault(); }}>
                      <Download className="h-4 w-4 mr-1" /> Download
                    </a>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline mock */}
          <div className="mt-3 text-xs text-muted-foreground">Timeline markers (mock): nearby detections within ±30s highlighted.</div>
        </section>

        {/* Details */}
        <aside className="lg:col-span-4 space-y-3">
          <Card>
            <CardContent className="p-4">
              <div className="text-sm mb-2">Labels</div>
              <div className="flex flex-wrap gap-1.5">
                {alert.labels.map((t, i) => (
                  <Badge key={i} variant="outline">{t}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 space-y-2">
              <div className="text-sm">Add note</div>
              <Textarea
                value={note}
                onChange={(e) => setNoteState(e.target.value)}
                placeholder="Add context for this alert..."
                className="min-h-[100px]"
              />
              <div className="flex justify-end">
                <Button size="sm" onClick={() => setNote(alert.alertId, note)}>Save note</Button>
              </div>
            </CardContent>
          </Card>

          {related.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <div className="text-sm mb-2">Related alerts</div>
                <div className="space-y-2">
                  {related.map((r) => (
                    <Link key={r.alertId} to={`/live/review/${r.alertId}`} className="block text-sm hover:underline">
                      {r.timestamp} · <span className="opacity-70">{r.category}</span> · {Math.round(r.confidence * 100)}%
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </aside>
      </div>
    </main>
  );
};

export default LiveReviewPage;

// Video player with visibility-based pause/resume
const VideoWithVisibility: React.FC<{ src: string; poster?: string; muted: boolean; playing: boolean; onPlayChange: (p: boolean) => void; }> = ({ src, poster, muted, playing, onPlayChange }) => {
  const ref = React.useRef<HTMLVideoElement | null>(null);
  React.useEffect(() => {
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver((entries) => {
      const e = entries[0];
      const inView = e?.isIntersecting || e?.intersectionRatio > 0;
      if (!inView) {
        try { el.pause(); onPlayChange(false); } catch {}
      } else if (playing) {
        try { el.play(); } catch {}
      }
    }, { rootMargin: "200px", threshold: [0, 0.01, 0.5, 1] });
    obs.observe(el);
    return () => obs.disconnect();
  }, [playing]);

  React.useEffect(() => {
    const el = ref.current; if (!el) return;
    if (playing) { try { el.play(); } catch {} } else { try { el.pause(); } catch {} }
  }, [playing]);

  return (
    <video
      ref={ref}
      src={src}
      poster={poster}
      autoPlay={playing}
      muted={muted}
      controls
      controlsList="nodownload noplaybackrate"
      style={{ width: "100%", height: "auto" }}
      onPlay={() => onPlayChange(true)}
      onPause={() => onPlayChange(false)}
    />
  );
};
