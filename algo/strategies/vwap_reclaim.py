"""VWAP reclaim, long only: on a green day, the first bar after `start_after` that closes back above
session VWAP after the previous bar closed below it. Stop under the recent swing low."""
from __future__ import annotations

from typing import Optional

from ..models import Signal, round_tick
from ..timeutil import hhmm


def session_vwap(bars: list) -> list:
    out, pv, vol = [], 0.0, 0.0
    for b in bars:
        typical = (b.high + b.low + b.close) / 3
        pv += typical * b.volume
        vol += b.volume
        out.append(pv / vol if vol > 0 else None)
    return out


def vwap_reclaim(symbol: str, bars: list, cfg: dict) -> Optional[Signal]:
    p = cfg["vwap_reclaim"]
    tick = cfg["tick_size"]
    if len(bars) < p["lookback_bars"] + 1 or bars[0].ts.time() != hhmm(cfg["session_open"]):
        return None
    vw = session_vwap(bars)
    start = hhmm(p["start_after"])
    day_open = bars[0].open

    for i in range(max(1, p["lookback_bars"] - 1), len(bars)):
        b, prev = bars[i], bars[i - 1]
        if b.ts.time() < start or vw[i] is None or vw[i - 1] is None:
            continue
        if not (prev.close < vw[i - 1] and b.close > vw[i] and b.close > day_open):
            continue
        entry = round_tick(b.close, tick)
        swing_low = min(x.low for x in bars[i - p["lookback_bars"] + 1:i + 1])
        stop = round_tick(swing_low, tick, "down")
        if (entry - stop) / entry * 100 < p["min_stop_pct"]:
            return None  # stop inside the noise: skip rather than widen it artificially
        target = round_tick(entry + p["target_r"] * (entry - stop), tick, "up")
        return Signal(symbol, "vwap_reclaim", entry, stop, target, b.ts,
                      "reclaimed VWAP %.2f, day open %.2f" % (vw[i], day_open))
    return None
