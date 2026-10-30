"""Pullback, long only: a strong open, then the first dip to session VWAP that closes back above it."""
from __future__ import annotations

from typing import Optional

from ..models import Signal, round_tick
from ..timeutil import hhmm
from .vwap_reclaim import session_vwap


def pullback(symbol: str, bars: list, cfg: dict) -> Optional[Signal]:
    p = cfg["pullback"]
    tick = cfg["tick_size"]
    if len(bars) < 4 or bars[0].ts.time() != hhmm(cfg["session_open"]):
        return None
    vw = session_vwap(bars)
    start = hhmm(p["start_after"])
    day_open = bars[0].open
    strong = False
    for i, b in enumerate(bars):
        if b.ts.time() < start:
            strong = strong or (b.close - day_open) / day_open * 100 >= p["min_open_move_pct"]
            continue
        if not strong:
            return None
        if vw[i] is None or not (b.low <= vw[i] < b.close and b.close > b.open):
            continue
        entry = round_tick(b.close, tick)
        stop = round_tick(min(x.low for x in bars[max(0, i - 2):i + 1]), tick, "down")
        if (entry - stop) / entry * 100 < p["min_stop_pct"]:
            return None
        target = round_tick(entry + p["target_r"] * (entry - stop), tick, "up")
        return Signal(symbol, "pullback", entry, stop, target, b.ts, "dip to VWAP %.2f held" % vw[i])
    return None
