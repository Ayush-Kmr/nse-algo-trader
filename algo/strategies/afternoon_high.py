"""Afternoon momentum, long only: after `start_after`, the first close at a new day high on a stock
already up on the day, above session VWAP. Stop at VWAP; a distant target leaves it to the square-off."""
from __future__ import annotations

from typing import Optional

from ..models import Signal, round_tick
from ..timeutil import hhmm
from .vwap_reclaim import session_vwap


def afternoon_high(symbol: str, bars: list, cfg: dict) -> Optional[Signal]:
    p = cfg["afternoon_high"]
    tick = cfg["tick_size"]
    if len(bars) < 2 or bars[0].ts.time() != hhmm(cfg["session_open"]):
        return None
    vw = session_vwap(bars)
    start = hhmm(p["start_after"])
    day_open = bars[0].open
    high = bars[0].high
    for i, b in enumerate(bars[1:], 1):
        if b.ts.time() >= start and vw[i] is not None and b.close > high and b.close > vw[i] \
                and (b.close - day_open) / day_open * 100 >= p["min_day_move_pct"]:
            entry = round_tick(b.close, tick)
            stop = round_tick(vw[i], tick, "down")
            if (entry - stop) / entry * 100 < p["min_stop_pct"]:
                return None
            target = round_tick(entry + p["target_r"] * (entry - stop), tick, "up")
            return Signal(symbol, "afternoon_high", entry, stop, target, b.ts, "new day high above VWAP")
        high = max(high, b.high)
    return None
