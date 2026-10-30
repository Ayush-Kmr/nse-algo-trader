"""Mean reversion, long only: stretched below session VWAP, then a bar closes above the prior high.
The target is VWAP itself. Meant to run without the green-day filter."""
from __future__ import annotations

from typing import Optional

from ..models import Signal, round_tick
from ..timeutil import hhmm
from .vwap_reclaim import session_vwap


def vwap_revert(symbol: str, bars: list, cfg: dict) -> Optional[Signal]:
    p = cfg["vwap_revert"]
    tick = cfg["tick_size"]
    if len(bars) < 4 or bars[0].ts.time() != hhmm(cfg["session_open"]):
        return None
    vw = session_vwap(bars)
    start = hhmm(p["start_after"])
    for i in range(3, len(bars)):
        b, prev = bars[i], bars[i - 1]
        if b.ts.time() < start or vw[i] is None or vw[i - 1] is None:
            continue
        if (vw[i - 1] - prev.close) / vw[i - 1] * 100 < p["min_stretch_pct"] or b.close <= prev.high:
            continue
        entry = round_tick(b.close, tick)
        stop = round_tick(min(x.low for x in bars[i - 2:i + 1]), tick, "down")
        target = round_tick(vw[i], tick)
        if (entry - stop) / entry * 100 < p["min_stop_pct"] or target - entry < p["min_reward_r"] * (entry - stop):
            return None
        return Signal(symbol, "vwap_revert", entry, stop, target, b.ts, "stretched below VWAP %.2f" % vw[i])
    return None
