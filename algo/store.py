"""Validated bar storage. Validation reports problems and drops nothing silently; gaps stay gaps."""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, time

from .models import Bar
from .timeutil import IST, now_ist


def validate(symbol: str, bars: list, minutes: int) -> dict:
    """-> {"bars", "bad": [...], "gaps": [...], "ok"}. Bad bars are named so they can be excluded."""
    bad, gaps, seen = [], [], set()
    prev = None
    for b in bars:
        why = []
        if b.ts.utcoffset().total_seconds() != 19800:
            why.append("not IST")
        if b.ts in seen:
            why.append("duplicate")
        if prev is not None and b.ts <= prev.ts:
            why.append("out of order")
        if not (b.low <= min(b.open, b.close) and b.high >= max(b.open, b.close)) or b.low <= 0:
            why.append("impossible OHLC")
        if b.volume < 0:
            why.append("negative volume")
        if not time(9, 15) <= b.ts.time() < time(15, 30):
            why.append("outside session")
        if why:
            bad.append((b.ts.isoformat(), ", ".join(why)))
        elif prev is not None and b.ts.date() == prev.ts.date() and (b.ts - prev.ts).total_seconds() != minutes * 60:
            gaps.append((prev.ts.isoformat(), b.ts.isoformat()))
        seen.add(b.ts)
        prev = b
    return {"symbol": symbol, "bars": len(bars), "bad": bad, "gaps": gaps, "ok": not bad}


def clean(bars: list, report: dict) -> list:
    bad = {t for t, _ in report["bad"]}
    return [b for b in bars if b.ts.isoformat() not in bad]


def save(root: str, source: str, symbol: str, bars: list, minutes: int, report: dict) -> str:
    folder = os.path.join(root, source, "%dm" % minutes)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, symbol.replace("^", "_") + ".csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts_ist", "open", "high", "low", "close", "volume"])
        w.writerows([b.ts.isoformat(), b.open, b.high, b.low, b.close, b.volume] for b in bars)
    with open(path + ".meta.json", "w") as fh:
        json.dump({"source": source, "symbol": symbol, "interval_minutes": minutes, "timezone": "Asia/Kolkata",
                   "fetched_at": now_ist().isoformat(), "bars": report["bars"], "bad_bars": len(report["bad"]),
                   "gaps": len(report["gaps"])}, fh, indent=1)
    return path


def load(path: str, minutes: int) -> list:
    with open(path, newline="") as fh:
        return [Bar(datetime.fromisoformat(r["ts_ist"]).astimezone(IST), float(r["open"]), float(r["high"]), float(r["low"]),
                    float(r["close"]), float(r["volume"]), minutes) for r in csv.DictReader(fh)]
