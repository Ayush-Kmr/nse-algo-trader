"""Indicators for one day of bars. Every value at index i uses only bars up to i."""
from __future__ import annotations

import statistics

from .extra import _ema as ema
from .extra import _rsi as rsi
from .strategies.vwap_reclaim import session_vwap


def atr(bars: list, n: int = 14) -> list:
    out, value = [], None
    for i, b in enumerate(bars):
        tr = b.high - b.low if i == 0 else max(b.high - b.low, abs(b.high - bars[i - 1].close), abs(b.low - bars[i - 1].close))
        value = tr if value is None else (value * (n - 1) + tr) / n
        out.append(value)
    return out


def relative_volume(bars: list, past_days: list) -> list:
    """Volume so far today against the same time of day on up to 20 earlier sessions."""
    out, total = [], 0.0
    for i, b in enumerate(bars):
        total += b.volume
        prior = [sum(x.volume for x in day[:i + 1]) for day in past_days[-20:] if len(day) > i]
        base = statistics.median(prior) if prior else 0
        out.append(total / base if base > 0 else None)
    return out


def market_direction(index_bars: list) -> dict:
    """{bar start: +1 if the index is above its day's open, else -1}. Uses bars up to that time."""
    if not index_bars:
        return {}
    o = index_bars[0].open
    return {b.ts: 1 if b.close > o else -1 for b in index_bars}


def compute(bars: list, past_days: list, index_bars: list) -> dict:
    c = [b.close for b in bars]
    return {"vwap": session_vwap(bars), "ema9": ema(c, 9), "ema20": ema(c, 20), "ema50": ema(c, 50), "rsi": rsi(c), "atr": atr(bars),
            "rvol": relative_volume(bars, past_days), "market": market_direction(index_bars)}
