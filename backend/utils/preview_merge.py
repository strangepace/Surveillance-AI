#!/usr/bin/env python3
"""
Utilities for merging per-label detection timestamps into continuous runs
and cutting preview clips using FFmpeg.

This module is pure-Python for merging logic and delegates media cutting to
`utils.ffmpeg` to ensure browser-safe encodes (H.264 MP4).
"""

from __future__ import annotations

import math
import os
import re
from typing import Dict, List, Tuple

from .ffmpeg import transcode_segment, get_video_info


def ts_to_seconds(ts: str) -> float:
    parts = ts.split(":")
    if len(parts) != 3:
        return 0.0
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_ts(x: float) -> str:
    x = max(0.0, x)
    hours = int(x // 3600)
    minutes = int((x % 3600) // 60)
    seconds = x % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"  # keep milliseconds


def merge_detections_by_label(
    detections: List[Dict], gap_s: float
) -> Dict[str, List[Dict]]:
    # Explode detections so each (timestamp, label, confidence) is a row
    rows: List[Tuple[float, str, float]] = []
    for d in detections:
        ts = d.get("timestamp") or d.get("time") or "00:00:00.000"
        t = ts_to_seconds(ts)
        labels = d.get("labels", []) or []
        conf = float(d.get("confidence", 0.0))
        for label in labels:
            rows.append((t, str(label), conf))

    rows.sort(key=lambda r: (r[1], r[0]))

    runs: Dict[str, List[Dict]] = {}
    last_time_for_label: Dict[str, float] = {}

    for t, label, conf in rows:
        if label not in runs or not runs[label]:
            runs.setdefault(label, []).append({
                "start_s": t,
                "end_s": t,
                "peak_conf": conf,
            })
            last_time_for_label[label] = t
            continue

        prev_end = last_time_for_label[label]
        if t - prev_end <= gap_s:
            # extend current run
            cur = runs[label][-1]
            cur["end_s"] = t
            cur["peak_conf"] = max(cur.get("peak_conf", 0.0), conf)
        else:
            # new run
            runs[label].append({
                "start_s": t,
                "end_s": t,
                "peak_conf": conf,
            })
        last_time_for_label[label] = t

    # Normalize zero-length runs to tiny positive durations (handled later)
    for label, items in runs.items():
        for r in items:
            if r["end_s"] < r["start_s"]:
                r["end_s"] = r["start_s"]

    return runs


def pad_and_cap(
    runs: List[Dict],
    pad_pre: float,
    pad_post: float,
    min_s: float,
    max_s: float,
    video_len_s: float,
) -> List[Dict]:
    padded: List[Dict] = []
    for r in runs:
        start = max(0.0, r["start_s"] - pad_pre)
        end = min(video_len_s, r["end_s"] + pad_post)
        # ensure minimum
        if end - start < min_s:
            center = (start + end) / 2.0
            start = max(0.0, center - min_s / 2.0)
            end = min(video_len_s, start + min_s)

        duration = max(0.0, end - start)
        if duration <= max_s:
            padded.append({"start_s": start, "end_s": end, "peak_conf": r.get("peak_conf", 0.0)})
        else:
            # split into chunks of max_s with 1s overlap
            cur = start
            while cur < end:
                seg_end = min(end, cur + max_s)
                padded.append({"start_s": cur, "end_s": seg_end, "peak_conf": r.get("peak_conf", 0.0)})
                if seg_end >= end:
                    break
                cur = seg_end - 1.0  # 1s overlap
    return padded


def sanitize_label(label: str) -> str:
    s = label.lower().strip().replace(" ", "_")
    return re.sub(r"[^a-z0-9_]", "", s)


def ffmpeg_cut_segment(src: str, start_s: float, end_s: float, out_path: str) -> bool:
    duration = max(0.0, end_s - start_s)
    if duration <= 0.01:
        return False
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    mp4_ok, _ = transcode_segment(src=src, start_sec=start_s, duration=duration, out_mp4=out_path)
    return bool(mp4_ok and os.path.exists(out_path))


def get_video_duration_seconds(src: str) -> float:
    info = get_video_info(src)
    if info and "format" in info and "duration" in info["format"]:
        try:
            return float(info["format"]["duration"])
        except Exception:
            pass
    return 0.0


