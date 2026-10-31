"""Free, official NSE daily bhavcopy files: every traded stock, including ones that later delisted.

This is the survivorship-free source for the delivery test. NSE's previous close is NOT adjusted on
ex-dates (Reliance's 2017 bonus shows 1645 to 818), so raw ratios turn splits into crashes. Daily
returns therefore come from Yahoo's split-adjusted closes where Yahoo has the stock. For delisted
stocks, a large one-day move counts as a corporate action only if it matches a clean split or bonus
ratio, so real crashes stay in. Keeps EQ plus the BE and BZ surveillance series, where troubled stocks end up. Dated membership of the
index is still unavailable, so the universe is each month's most-traded stocks. Downloads resume from
data/bhav/ and run a few at a time.
"""
from __future__ import annotations

import csv
import gzip
import io
import os
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://nsearchives.nseindia.com/content"
SERIES = ("EQ", "BE", "BZ")
NOT_STOCKS = ("BEES", "ETF", "IETF", "GOLD", "LIQUID")


def urls(d: date) -> list:
    old = "%s/historical/EQUITIES/%d/%s/cm%s%s%dbhav.csv.zip" % (
        BASE, d.year, d.strftime("%b").upper(), d.strftime("%d"), d.strftime("%b").upper(), d.year)
    new = "%s/cm/BhavCopy_NSE_CM_0_0_0_%s_F_0000.csv.zip" % (BASE, d.strftime("%Y%m%d"))
    return [new, old] if d >= date(2024, 7, 1) else [old, new]


def parse(raw: bytes) -> list:
    """Zip bytes -> [(symbol, close, prevclose, value traded)] for stocks."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8", "replace")
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
        new = "TckrSymb" in r
        sym, series = (r["TckrSymb"], r["SctySrs"]) if new else (r["SYMBOL"], r["SERIES"])
        if series not in SERIES:
            continue
        try:
            row = (r["ClsPric"], r["PrvsClsgPric"], r["TtlTrfVal"]) if new else (r["CLOSE"], r["PREVCLOSE"], r["TOTTRDVAL"])
            out.append((sym, float(row[0]), float(row[1]), float(row[2])))
        except ValueError:
            continue
    return out


def _path(root: str, d: date) -> str:
    return os.path.join(root, d.isoformat() + ".csv.gz")


def download_day(root: str, d: date) -> str:
    path = _path(root, d)
    if os.path.exists(path):
        return "cached"
    for url in urls(d):
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=30) as r:
                    rows = parse(r.read())
                tmp = path + ".tmp"
                with gzip.open(tmp, "wt") as fh:
                    csv.writer(fh).writerows(rows)
                os.replace(tmp, path)
                return "ok"
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                time.sleep(2 * (attempt + 1))
            except Exception:  # noqa: BLE001 - retried, then reported as missing
                time.sleep(2 * (attempt + 1))
    return "missing"


def download(root: str, start: date, end: date, workers: int = 3) -> dict:
    os.makedirs(root, exist_ok=True)
    days = [start + timedelta(days=k) for k in range((end - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    counts = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for k, result in enumerate(pool.map(lambda d: download_day(root, d), days)):
            counts[result] = counts.get(result, 0) + 1
            if k % 500 == 0:
                print("  %d of %d: %s" % (k, len(days), counts), flush=True)
    return counts


SPLIT_RATIOS = (1 / 2, 1 / 3, 1 / 4, 1 / 5, 1 / 10, 2 / 3, 3 / 4)


def looks_like_split(ratio: float) -> bool:
    return ratio <= 0.8 and any(abs(ratio / r - 1) < 0.04 for r in SPLIT_RATIOS)


def load(root: str) -> tuple:
    """-> ({symbol: [(date, close / prevclose)]}, {symbol: {date: rupees traded}})"""
    moves, traded = {}, {}
    for name in sorted(os.listdir(root)):
        if not name.endswith(".csv.gz"):
            continue
        d = date.fromisoformat(name[:10])
        seen = set()
        with gzip.open(os.path.join(root, name), "rt") as fh:
            for sym, close, prev, value in csv.reader(fh):
                if sym in seen:  # a stock appears in one series a day; ignore any repeat
                    continue
                seen.add(sym)
                close, prev = float(close), float(prev)
                if close <= 0 or prev <= 0:
                    continue
                moves.setdefault(sym, []).append((d, close / prev))
                traded.setdefault(sym, {})[d] = float(value)
    return moves, traded


def adjusted(moves: dict, yahoo: dict = None) -> dict:
    """{symbol: {date: level}}, starting at 100. yahoo: {symbol: {date: split-adjusted close}}."""
    yahoo = yahoo or {}
    out = {}
    for sym, days in moves.items():
        known, level, prev_day, series = yahoo.get(sym), 100.0, None, {}
        for d, ratio in days:
            if known and d in known and prev_day in known:
                level *= known[d] / known[prev_day]
            elif not looks_like_split(ratio) and ratio < 1.4:
                level *= ratio
            series[d] = level
            prev_day = d
        out[sym] = series
    return out


def stocks_only(symbols) -> list:
    return [s for s in symbols if not any(x in s for x in NOT_STOCKS)]
