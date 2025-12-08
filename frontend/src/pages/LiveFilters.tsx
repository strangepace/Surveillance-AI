import React from "react";
import { SEOHead } from "@/components/SEO";
import { useLiveStore, Category } from "@/context/LiveStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useNavigate } from "react-router-dom";

const ALL_CATEGORIES: Category[] = ["people", "color", "fire", "vehicle", "weapon", "activity"];

const LiveFiltersPage: React.FC = () => {
  const navigate = useNavigate();
  const { alerts, filters, setFilters } = useLiveStore();

  // derive camera ids from alerts
  const cameraIds = React.useMemo(() => Array.from(new Set(alerts.map((a) => a.cameraId))).sort(), [alerts]);

  const [draft, setDraft] = React.useState({
    categories: new Set<Category>(filters.categories),
    search: filters.search,
    sort: filters.sort,
    confidenceRange: [...filters.confidenceRange] as [number, number],
    timeRange: filters.timeRange,
    cameraId: filters.cameraId ?? null,
  });

  const toggleCat = (c: Category) => {
    setDraft((prev) => {
      const next = new Set(prev.categories);
      if (next.has(c)) next.delete(c);
      else next.add(c);
      return { ...prev, categories: next };
    });
  };

  const setPresetCommon = () => {
    setDraft((prev) => ({ ...prev, categories: new Set<Category>(["people", "vehicle", "activity", "fire"]) }));
  };

  const onApply = () => {
    setFilters({
      categories: draft.categories,
      search: draft.search,
      sort: draft.sort,
      confidenceRange: draft.confidenceRange,
      timeRange: draft.timeRange,
      cameraId: draft.cameraId,
    });
    // Navigate to alerts with URL reflecting key parts
    const params = new URLSearchParams();
    if (draft.categories.size) params.set("filters", Array.from(draft.categories).join(","));
    if (draft.search) params.set("q", draft.search);
    if (draft.sort) params.set("sort", draft.sort);
    navigate(`/live/alerts?${params.toString()}`);
  };

  const onReset = () => {
    setDraft({
      categories: new Set<Category>(),
      search: "",
      sort: "newest",
      confidenceRange: [0, 1],
    timeRange: "10m",
      cameraId: null,
    });
  };

  return (
    <main>
      <SEOHead title="Live Filters – Surveillance AI" description="Configure live alerts filters, confidence, time and camera." />
      <Sheet open onOpenChange={() => navigate(-1)}>
        <SheetContent side="right" className="w-[400px] sm:w-[480px]" onOpenAutoFocus={(e) => { e.preventDefault(); setTimeout(() => { (document.querySelector('[data-first-focus]') as HTMLElement | null)?.focus(); }, 10); }}>
          <SheetHeader>
            <SheetTitle>Filters</SheetTitle>
          </SheetHeader>
          <div className="mt-4 space-y-6">
            {/* Categories */}
            <section>
              <Label className="text-sm">Categories</Label>
              <div className="mt-2 flex flex-wrap gap-2">
                {ALL_CATEGORIES.map((c, idx) => {
                  const active = draft.categories.has(c);
                  return (
                    <Button key={c} size="sm" variant={active ? "secondary" : "outline"} onClick={() => toggleCat(c)} aria-pressed={active} data-first-focus={idx === 0 ? true : undefined}>
                      {c}
                    </Button>
                  );
                })}
              </div>
              <div className="mt-2 flex gap-2">
                <Button size="sm" variant="ghost" onClick={() => setDraft((p) => ({ ...p, categories: new Set() }))}>Clear</Button>
                <Button size="sm" variant="ghost" onClick={setPresetCommon}>Common</Button>
              </div>
            </section>

            {/* Confidence */}
            <section>
              <Label className="text-sm">Confidence</Label>
              <div className="mt-3 px-1">
                <Slider
                  value={[Math.round(draft.confidenceRange[0] * 100), Math.round(draft.confidenceRange[1] * 100)]}
                  min={0}
                  max={100}
                  step={1}
                  onValueChange={([lo, hi]) => setDraft((p) => ({ ...p, confidenceRange: [lo / 100, hi / 100] }))}
                  aria-describedby="confidence-help"
                />
                <div id="confidence-help" className="mt-1 text-xs text-muted-foreground">{Math.round(draft.confidenceRange[0] * 100)}% – {Math.round(draft.confidenceRange[1] * 100)}%</div>
              </div>
            </section>

            {/* Time range */}
            <section>
              <Label className="text-sm">Time range</Label>
              <div className="mt-2">
                <Select value={draft.timeRange} onValueChange={(v) => setDraft((p) => ({ ...p, timeRange: v as any }))}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Select" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30s">Last 30 seconds</SelectItem>
                    <SelectItem value="2m">Last 2 minutes</SelectItem>
                    <SelectItem value="10m">Last 10 minutes</SelectItem>
                    <SelectItem value="1h">Last 1 hour</SelectItem>
                    <SelectItem value="24h">Last 24 hours</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </section>

            {/* Camera */}
            <section>
              <Label className="text-sm">Camera</Label>
              <div className="mt-2">
                <Select value={draft.cameraId ?? ""} onValueChange={(v) => setDraft((p) => ({ ...p, cameraId: v || null }))}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="All cameras" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All cameras</SelectItem>
                    {cameraIds.map((id) => (
                      <SelectItem key={id} value={id}>{id}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </section>

            {/* Apply/Reset */}
            <div className="flex justify-between gap-2 pt-2">
              <Button variant="ghost" onClick={onReset}>Reset</Button>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
                <Button onClick={() => { sessionStorage.setItem("live.returnFocus", "#alerts-list :focus"); onApply(); }}>Apply</Button>
              </div>
            </div>

            {/* Active summary */}
            <div className="pt-2">
              <div className="text-xs text-muted-foreground mb-1">Active</div>
              <div className="flex flex-wrap gap-1.5">
                {Array.from(draft.categories).map((c) => <Badge key={c} variant="outline">{c}</Badge>)}
                {draft.cameraId && <Badge variant="outline">cam:{draft.cameraId}</Badge>}
                <Badge variant="outline">{Math.round(draft.confidenceRange[0] * 100)}–{Math.round(draft.confidenceRange[1] * 100)}%</Badge>
                <Badge variant="outline">{draft.timeRange}</Badge>
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </main>
  );
};

export default LiveFiltersPage;
