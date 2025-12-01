import json
import os
import threading
import time
import hashlib
from typing import Optional, Dict, Any


REGISTRY_DIR = os.path.join("content", "uploads")
REGISTRY_PATH = os.path.join(REGISTRY_DIR, "media_registry.json")
_lock = threading.Lock()


def init_registry() -> None:
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    if not os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump({"items": {}}, f)


def _load() -> Dict[str, Any]:
    if not os.path.exists(REGISTRY_PATH):
        return {"items": {}}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"items": {}}


def _save(data: Dict[str, Any]) -> None:
    tmp = REGISTRY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, REGISTRY_PATH)


def make_media_id(url: str, format_id: Optional[str]) -> str:
    key = f"{url}|{format_id or 'auto'}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"yt_{h}"


def upsert_media(record: Dict[str, Any]) -> None:
    init_registry()
    with _lock:
        data = _load()
        media_id = record["media_id"]
        record["updated_at"] = int(time.time())
        if media_id not in data["items"]:
            record["created_at"] = record["updated_at"]
        data["items"][media_id] = record
        _save(data)


def get_by_id(media_id: str) -> Optional[Dict[str, Any]]:
    init_registry()
    with _lock:
        data = _load()
        return data["items"].get(media_id)


def find_by_key(url: str, format_id: Optional[str]) -> Optional[Dict[str, Any]]:
    init_registry()
    with _lock:
        data = _load()
        for item in data["items"].values():
            if item.get("source") == "youtube" and item.get("url") == url and item.get("format_id") == (format_id or "auto"):
                return item
        return None


def touch(media_id: str) -> None:
    init_registry()
    with _lock:
        data = _load()
        if media_id in data["items"]:
            data["items"][media_id]["updated_at"] = int(time.time())
            _save(data)


def total_size_gb() -> float:
    total_bytes = 0
    for root, _, files in os.walk(os.path.join("content", "uploads")):
        for name in files:
            try:
                total_bytes += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total_bytes / (1024 * 1024 * 1024)


def evict_if_needed(max_total_gb: float) -> None:
    """No-op stub for future eviction (LRU)."""
    # TODO: Implement LRU based on updated_at and size_bytes
    _ = max_total_gb
    return None

