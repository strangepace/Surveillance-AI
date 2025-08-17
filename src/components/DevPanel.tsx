import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useLiveStore, Category } from "@/context/LiveStore";
import flags from "@/lib/config";

const ALL_CATEGORIES: Category[] = ["people", "color", "fire", "vehicle", "weapon", "activity"];

const DevPanel: React.FC = () => {
  const [open, setOpen] = React.useState(false);
  const [mock, setMock] = React.useState<boolean>(() => localStorage.getItem("dev.mockResults") === "1");
  const [slow, setSlow] = React.useState<boolean>(() => localStorage.getItem("dev.slowMode") === "1");
  const [hc, setHc] = React.useState<boolean>(() => localStorage.getItem("ui.highContrast") === "1" || document.documentElement.classList.contains("high-contrast"));
  const [heroFallback, setHeroFallback] = React.useState<boolean>(() => localStorage.getItem("ui.heroForceFallback") === "1");

  let store: ReturnType<typeof useLiveStore> | null = null;
  try { store = useLiveStore(); } catch { store = null; }
  if (!store) return null;
  const { dev, setDevOptions, clear } = store;


  const toggleMock = (v: boolean) => {
    setMock(v);
    setDevOptions({ useRealApi: !(flags.enableLiveMock || v) });
    try { localStorage.setItem("dev.mockResults", v ? "1" : "0"); } catch {}
  };
  const toggleSlow = (v: boolean) => {
    setSlow(v);
    try { localStorage.setItem("dev.slowMode", v ? "1" : "0"); } catch {}
  };
  const toggleHc = (v: boolean) => {
    setHc(v);
    if (v) document.documentElement.classList.add("high-contrast");
    else document.documentElement.classList.remove("high-contrast");
    try { localStorage.setItem("ui.highContrast", v ? "1" : "0"); } catch {}
  };

  const toggleHero = (v: boolean) => {
    setHeroFallback(v);
    try { localStorage.setItem("ui.heroForceFallback", v ? "1" : "0"); } catch {}
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="flex justify-end">
        <Button size="sm" variant="secondary" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="dev-panel">
          Dev
        </Button>
      </div>
      {open && (
        <Card id="dev-panel" className="mt-2 w-80 shadow-lg">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Developer Tools</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="dev-mock" className="text-sm">Mock Results</Label>
              <Switch id="dev-mock" checked={flags.enableLiveMock || mock} disabled={flags.enableLiveMock} onCheckedChange={toggleMock} />
            </div>
            {flags.enableLiveMock && <div className="text-[11px] text-muted-foreground">Forced by env (NEXT_PUBLIC_ENABLE_MOCKS=true)</div>}
            <div className="flex items-center justify-between">
              <Label htmlFor="dev-slow" className="text-sm">Slow Mode</Label>
              <Switch id="dev-slow" checked={slow} onCheckedChange={toggleSlow} />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="dev-hc" className="text-sm">High Contrast</Label>
              <Switch id="dev-hc" checked={hc} onCheckedChange={toggleHc} />
            </div>

            {/* Landing hero (QA) */}
            <div className="pt-2 border-t space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="dev-hero-fallback" className="text-sm">Force static hero</Label>
                <Switch id="dev-hero-fallback" checked={heroFallback} onCheckedChange={(v) => {
                  setHeroFallback(v);
                  try { localStorage.setItem("ui.heroForceFallback", v ? "1" : "0"); } catch {}
                }} />
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => { try { sessionStorage.removeItem("hero.seen"); } catch {}; window.location.assign("/"); }}>
                  Replay intro
                </Button>
                {import.meta.env.DEV && (
                  <Button size="sm" variant="outline" onClick={() => window.location.assign("/verify")}>Verify</Button>
                )}
              </div>
            </div>

            {/* Live sim controls */}
            <div className="pt-2 border-t space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="dev-jitter" className="text-sm">Jitter FPS</Label>
                <Switch id="dev-jitter" checked={dev.jitterFps} onCheckedChange={(v) => setDevOptions({ jitterFps: v })} />
              </div>
              <div>
                <div className="text-xs mb-1">Simulate categories</div>
                <div className="flex flex-wrap gap-2">
                  {ALL_CATEGORIES.map((c) => (
                    <Button
                      key={c}
                      size="sm"
                      variant={dev.simCategories[c] ? "secondary" : "outline"}
                      onClick={() => setDevOptions({ simCategories: { ...dev.simCategories, [c]: !dev.simCategories[c] } })}
                    >
                      {c}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="default"
                  onClick={() => {
                    try { window.dispatchEvent(new CustomEvent("dev:live-burst")); } catch {}
                  }}
                >
                  Simulate burst
                </Button>
                <Button size="sm" variant="outline" onClick={() => clear()}>Clear alerts</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DevPanel;
