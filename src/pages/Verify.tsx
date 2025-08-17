import React from "react";
import { SEOHead } from "@/components/SEO";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, API_BASE, WS_BASE } from "@/lib/api";
import { LiveClient } from "@/lib/liveClient";

const VerifyPage: React.FC = () => {
  const [health, setHealth] = React.useState<any | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [cameraId, setCameraId] = React.useState<string>("");
  const [wsState, setWsState] = React.useState<string>("idle");
  const wsRef = React.useRef<LiveClient | null>(null);

  const onPing = async () => {
    setLoading(true);
    setError(null);
    setHealth(null);
    try {
      const h = await api.getHealth();
      setHealth(h);
    } catch (e: any) {
      setError(e?.message || "Ping failed");
    } finally {
      setLoading(false);
    }
  };

  const onWsTest = () => {
    try { wsRef.current?.disconnect(); } catch {}
    wsRef.current = new LiveClient();
    setWsState("connecting");
    wsRef.current.connect({
      cameraId,
      onAlert: () => {},
      onStatus: (s) => setWsState(s),
    });
    window.setTimeout(() => {
      setWsState((s) => (s === "connected" ? "connected (closed)" : `${s} (closed)`));
      try { wsRef.current?.disconnect(); } catch {}
    }, 10000);
  };

  return (
    <main className="container mx-auto p-4 md:p-6">
      <SEOHead title="Verify – Dev utilities" description="Quick environment verification for integration." />
      <h1 className="text-xl font-semibold mb-3">Verify (Dev Only)</h1>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Environment</CardTitle>
            <CardDescription>Values as read by the app.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div><span className="font-medium">API_BASE_URL:</span> <code>{API_BASE || "(relative)"}</code></div>
              <div><span className="font-medium">WS_BASE_URL:</span> <code>{WS_BASE || "(derived/relative)"}</code></div>
              <div className="text-muted-foreground text-xs mt-2">See README for .env setup.</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ping /health</CardTitle>
            <CardDescription>Fetches basic backend info.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mb-3">
              <Button onClick={onPing} disabled={loading}>{loading ? "Pinging…" : "Ping /health"}</Button>
              {error && <div className="text-xs text-destructive">{error}</div>}
            </div>
            {health && (
              <pre className="text-xs bg-muted rounded-md p-3 overflow-auto max-h-64">{JSON.stringify(health, null, 2)}</pre>
            )}
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>WebSocket Test</CardTitle>
            <CardDescription>Open a temporary connection for 10 seconds.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Input className="w-64" placeholder="cameraId (optional)" value={cameraId} onChange={(e) => setCameraId(e.target.value)} />
              <Button variant="outline" onClick={onWsTest}>Open WS</Button>
              <div className="text-xs">State: <span className="font-medium">{wsState}</span></div>
            </div>
            <div className="text-xs text-muted-foreground">Note: This page is intended for development verification and may be disabled in production.</div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
};

export default VerifyPage;
