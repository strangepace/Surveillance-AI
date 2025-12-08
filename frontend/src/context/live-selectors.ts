import { Alert, Category, LiveFilters, SortKey } from "./live-types";

export function nowTs(): number { return Math.floor(Date.now() / 1000); }

export function sortAlerts(alerts: Alert[], sort: SortKey): Alert[] {
  const arr = [...alerts];
  switch (sort) {
    case "oldest":
      return arr.sort((a, b) => a.tsUnix - b.tsUnix);
    case "confidence_asc":
      return arr.sort((a, b) => a.confidence - b.confidence);
    case "confidence_desc":
      return arr.sort((a, b) => b.confidence - a.confidence);
    case "newest":
    default:
      return arr.sort((a, b) => b.tsUnix - a.tsUnix);
  }
}

export function filterAlerts(alerts: Alert[], f: LiveFilters): Alert[] {
  const { categories, search, confidenceRange, timeRange, cameraId } = f;
  const [minC, maxC] = confidenceRange;
  const now = nowTs();
  const rangeSec =
    timeRange === "30s" ? 30 :
    timeRange === "2m" ? 120 :
    timeRange === "10m" ? 600 :
    timeRange === "1h" ? 3600 :
    timeRange === "24h" ? 86400 : 86400;
  const q = search.trim().toLowerCase();
  return alerts.filter((a) => {
    if (categories.size && !categories.has(a.category)) return false;
    if (a.confidence < minC || a.confidence > maxC) return false;
    if (cameraId && a.cameraId !== cameraId) return false;
    if (q && !(`${a.labels.join(" ")} ${a.category}`.toLowerCase().includes(q))) return false;
    if (now - a.tsUnix > rangeSec) return false;
    return true;
  });
}
