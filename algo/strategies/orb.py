"""Opening-range breakout, long only: the first completed bar that CLOSES above the opening range."""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Optional

from ..models import Signal, round_tick
from ..timeutil import hhmm


def orb(symbol: str, bars: list, cfg: dict) -> Optional[Signal]:
    p = cfg["orb"]
    tick = cfg["tick_size"]
    if not bars:
        return None
    open_t = hhmm(cfg["session_open"])
    first = bars[0]
    if first.ts.time() != open_t:
        return None  # missing the opening bar: cannot build an honest range

    or_end = datetime.combine(first.ts.date(), open_t, first.ts.tzinfo) + timedelta(minutes=p["opening_range_minutes"])
    rng = [b for b in bars if b.ts < or_end]
    if len(rng) * cfg["bar_minutes"] < p["opening_range_minutes"]:
        return None  # range still forming
    hi = max(b.high for b in rng)
    lo = min(b.low for b in rng)
    width_pct = (hi - lo) / lo * 100
    if not (p["min_range_pct"] <= width_pct <= p["max_range_pct"]):
        return None

    after = bars[len(rng):]
    for i, b in enumerate(after):
        if b.close <= hi:
            continue
        # Only the FIRST close above the range counts. A failed volume check means no trade today.
        if p.get("volume_mult"):
            prior = [x.volume for x in bars[1:len(rng) + i]]  # skip the opening auction bar
            if prior and b.volume < p["volume_mult"] * statistics.median(prior):
                return None
        entry = round_tick(b.close, tick)
        stop_raw = (hi + lo) / 2 if p["stop"] == "mid" else lo
        stop = round_tick(stop_raw, tick, "down")
        risk = entry - stop
        if risk <= 0:
            return None
        target = round_tick(entry + p["target_r"] * risk, tick, "up")
        return Signal(symbol, "orb", entry, stop, target, b.ts,
                      "closed %.2f above range %.2f-%.2f (%.2f%% wide)" % (b.close, lo, hi, width_pct))
    return None
