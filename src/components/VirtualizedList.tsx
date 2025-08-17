import React, { useDeferredValue } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useVirtualizer } from "@tanstack/react-virtual";
import LazyVideo from "@/components/LazyVideo";
import { Pin, PinOff, CheckCircle2 } from "lucide-react";

type ResultEntry = {
  timestamp: string;
  labels: string[];
  confidence: number;
  preview_clip: string;
};

function formatConf(n: number) {
  return `${Math.round(n * 100)}%`;
}

// Memoized row to avoid unnecessary re-renders
const RowCard = React.memo(function RowCard({
  item,
  index,
  isPinned,
  isAcked,
  onPin,
  onAck,
}: {
  item: ResultEntry;
  index: number;
  isPinned: boolean;
  isAcked: boolean;
  onPin: (i: number) => void;
  onAck: (i: number) => void;
}) {
  const ariaLabel = `${item.timestamp}. Labels: ${item.labels.slice(0, 3).join(", ")}`;
  return (
    <div role="listitem" aria-label={ariaLabel} className="p-2">
      <Card
        className={`relative transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md ${
          isPinned ? "ring-1 ring-primary/30" : ""
        } ${isAcked ? "opacity-90" : ""}`}
      >
        <CardHeader className="space-y-1 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">{item.timestamp}</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={isPinned ? "secondary" : "outline"}
                onClick={() => onPin(index)}
                aria-pressed={isPinned}
                aria-label={isPinned ? "Unpin alert" : "Pin alert"}
              >
                {isPinned ? <PinOff aria-hidden /> : <Pin aria-hidden />}
              </Button>
              <Button
                size="sm"
                variant={isAcked ? "secondary" : "outline"}
                onClick={() => onAck(index)}
                aria-checked={isAcked}
                role="checkbox"
                aria-label={isAcked ? "Unacknowledge alert" : "Acknowledge alert"}
              >
                <CheckCircle2 aria-hidden />
              </Button>
            </div>
          </div>
          <CardDescription>Confidence: {formatConf(item.confidence)}</CardDescription>
        </CardHeader>
        <CardContent>
          {isPinned && (
            <Badge variant="secondary" className="absolute left-2 top-2 z-10">
              Pinned
            </Badge>
          )}
          {isAcked && (
            <Badge variant="outline" className="absolute left-2 top-10 z-10">
              ✓ Acknowledged
            </Badge>
          )}
          <div className="overflow-hidden rounded-md border">
            <LazyVideo src={item.preview_clip} controls className="h-auto w-full" preload="metadata" playsInline />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {item.labels.map((l, k) => (
              <Badge key={k} variant="outline">
                {l}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}, areEqual);

function areEqual(prev: any, next: any) {
  // Compare only the fields that affect rendering
  if (prev.index !== next.index) return false;
  if (prev.isPinned !== next.isPinned) return false;
  if (prev.isAcked !== next.isAcked) return false;
  const a = prev.item as ResultEntry;
  const b = next.item as ResultEntry;
  if (a.timestamp !== b.timestamp) return false;
  if (a.confidence !== b.confidence) return false;
  if (a.preview_clip !== b.preview_clip) return false;
  if (a.labels.length !== b.labels.length) return false;
  for (let i = 0; i < a.labels.length; i++) if (a.labels[i] !== b.labels[i]) return false;
  return true;
}

export function VirtualizedList({
  items,
  pinned,
  acknowledged,
  onPin,
  onAck,
}: {
  items: ResultEntry[];
  pinned: Set<number>;
  acknowledged: Set<number>;
  onPin: (i: number) => void;
  onAck: (i: number) => void;
}) {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  // Dynamic overscan tuned by scroll velocity
  const [overscan, setOverscan] = React.useState<number>(8);
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
        const speed = dy / dt; // px per ms
        lastRef.current = { t: now, y };
        // Map speed to overscan (items). Slow -> small, fast -> larger
        // Assume ~360px row height
        const approxRowsPerMs = speed / 360;
        const target = Math.min(40, Math.max(6, Math.round(approxRowsPerMs * 120 + 8)));
        if (target !== overscan) setOverscan(target);
      });
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el.removeEventListener("scroll", onScroll as any);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [overscan]);

  // Defer heavy list updates during fast typing/filtering
  const deferredItems = useDeferredValue(items);

  const rowVirtualizer = useVirtualizer({
    count: deferredItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 360,
    overscan,
  });

  const virtualItems = rowVirtualizer.getVirtualItems();

  return (
    <div ref={parentRef} className="h-[70vh] overflow-auto rounded-md border" role="list" aria-label="Alerts list">
      <div style={{ height: rowVirtualizer.getTotalSize(), position: "relative" }}>
        {virtualItems.map((vi) => {
          const i = vi.index;
          const r = deferredItems[i];
          if (!r) return null;
          return (
            <div
              key={vi.key}
              style={{ transform: `translateY(${vi.start}px)`, position: "absolute", left: 0, right: 0 }}
            >
              <RowCard
                item={r}
                index={i}
                isPinned={pinned.has(i)}
                isAcked={acknowledged.has(i)}
                onPin={onPin}
                onAck={onAck}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
