"""Market data: Yahoo Finance chart endpoint (free, unofficial, delayed, can rate-limit).

Good enough for paper trading and backtests. Swap for SmartAPI candles before going live.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from .models import Bar
from .timeutil import IST

HOSTS = ("https://query2.finance.yahoo.com", "https://query1.finance.yahoo.com")
UA = "Mozilla/5.0 (compatible; nse-algo-trader/0.1)"


def yahoo_symbol(sym: str) -> str:
    return sym if sym.startswith("^") else sym + ".NS"


def _get_json(path: str, retries: int = 3, timeout: int = 20) -> dict:
    last = None
    for attempt in range(retries):
        for host in HOSTS:
            req = urllib.request.Request(host + path, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001 - any failure: try the other host, then back off
                last = e
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("yahoo fetch failed: %s" % last)


def fetch_bars(sym: str, range_: str = "5d", interval: str = "5m", retries: int = 3, timeout: int = 20) -> list:
    path = "/v8/finance/chart/%s?range=%s&interval=%s" % (
        urllib.parse.quote(yahoo_symbol(sym)), range_, interval)
    data = _get_json(path, retries, timeout)
    res = (data.get("chart") or {}).get("result") or []
    if not res:
        return []
    r = res[0]
    q = r["indicators"]["quote"][0]
    minutes = int(interval.rstrip("m"))
    bars = []
    for i, ts in enumerate(r.get("timestamp") or []):
        o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
        if None in (o, h, l, c):
            continue
        bars.append(Bar(datetime.fromtimestamp(ts, IST), float(o), float(h), float(l), float(c),
                        float(v or 0), minutes))
    return bars


def completed(bars: list, now: datetime, grace_seconds: int = 0) -> list:
    """Only bars that have fully closed. The live, still-forming bar is never used.

    The clock alone is not enough: Yahoo can lag, and a bar read too early is never re-read. So a bar
    counts once a later bar exists, or once `grace_seconds` have passed since it ended.
    """
    grace = timedelta(seconds=grace_seconds)
    return [b for i, b in enumerate(bars)
            if b.end + grace <= now or (i + 1 < len(bars) and bars[i + 1].ts >= b.end and b.end <= now)]


def by_day(bars: list) -> dict:
    out = defaultdict(list)
    for b in bars:
        out[b.ts.date()].append(b)
    return dict(out)


def save_history(path: str, history: dict) -> None:
    import os
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    rows = {s: [[b.ts.isoformat(), b.open, b.high, b.low, b.close, b.volume, b.minutes] for b in bars]
            for s, bars in history.items()}
    with open(path, "w") as fh:
        json.dump(rows, fh)


def load_history(path: str) -> dict:
    with open(path) as fh:
        rows = json.load(fh)
    return {s: [Bar(datetime.fromisoformat(r[0]), *r[1:]) for r in bars] for s, bars in rows.items()}


class YahooSource:
    def __init__(self, pause: float = 0.3):
        self.pause = pause

    def today(self, symbols, now: datetime, grace_seconds: int = 0):
        """-> ({symbol: completed bars today}, {symbol: error})"""
        def fetch(s):
            try:
                return s, fetch_bars(s, "1d", "5m", retries=2, timeout=8), None  # must fit the 4-minute job
            except Exception as e:  # noqa: BLE001
                return s, None, str(e)

        out, errors = {}, {}
        with ThreadPoolExecutor(max_workers=6) as pool:  # a few at a time: Yahoo rate-limits cloud IPs
            for s, bars, err in pool.map(fetch, symbols):
                if err is not None:
                    errors[s] = err
                else:
                    out[s] = [b for b in completed(bars, now, grace_seconds) if b.ts.date() == now.date()]
        return out, errors

    def history(self, symbols, range_: str = "60d"):
        out = {}
        for s in symbols:
            try:
                out[s] = fetch_bars(s, range_, "5m")
            except Exception as e:  # noqa: BLE001
                print("  skip %s: %s" % (s, e))
            time.sleep(self.pause)
        return out
