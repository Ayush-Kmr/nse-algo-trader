"""Broker market data: DhanHQ (primary) and Upstox (alternative). Read-only: no order endpoint exists here.

Tokens come from the environment: DHAN_ACCESS_TOKEN and DHAN_CLIENT_ID, or UPSTOX_ACCESS_TOKEN. Requests
are split to each API's limit: Dhan 90 days a call, Upstox one month for 1 to 15 minute bars.
"""
from __future__ import annotations

import csv
import io
import json
import os
import struct
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from .models import Bar
from .timeutil import IST

DHAN_INTRADAY = "https://api.dhan.co/v2/charts/intraday"
DHAN_WS = "wss://api-feed.dhan.co?version=2&token=%s&clientId=%s&authType=2"
DHAN_SCRIPS = "https://images.dhan.co/api-data/api-scrip-master.csv"
UPSTOX_CANDLES = "https://api.upstox.com/v3/historical-candle/%s/minutes/%d/%s/%s"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("%s is not set. No data was fetched, and none will be invented." % name)
    return value


def _windows(start: date, end: date, days: int) -> list:
    out, a = [], start
    while a <= end:
        b = min(end, a + timedelta(days=days - 1))
        out.append((a, b))
        a = b + timedelta(days=1)
    return out


def dhan_bars(payload: dict, minutes: int) -> list:
    keys = ("timestamp", "open", "high", "low", "close", "volume")
    columns = [payload.get(k) or [] for k in keys]
    if len({len(c) for c in columns}) != 1:
        raise ValueError("Dhan returned columns of different lengths")
    return [Bar(datetime.fromtimestamp(t, IST), float(o), float(h), float(l), float(c), float(v), minutes)
            for t, o, h, l, c, v in zip(*columns)]


def upstox_bars(payload: dict, minutes: int) -> list:
    rows = (payload.get("data") or {}).get("candles") or []
    return sorted((Bar(datetime.fromisoformat(r[0]).astimezone(IST), float(r[1]), float(r[2]), float(r[3]), float(r[4]),
                       float(r[5]), minutes) for r in rows), key=lambda b: b.ts)


class DhanSource:
    name = "dhan"

    def __init__(self):
        self.token = _require("DHAN_ACCESS_TOKEN")

    def history(self, security_id: str, start: date, end: date, minutes: int = 5) -> list:
        bars = []
        for a, b in _windows(start, end, 90):
            body = {"securityId": str(security_id), "exchangeSegment": "NSE_EQ", "instrument": "EQUITY", "interval": str(minutes),
                    "oi": False, "fromDate": "%s 09:15:00" % a, "toDate": "%s 15:30:00" % b}
            req = urllib.request.Request(DHAN_INTRADAY, data=json.dumps(body).encode(), headers={
                "Accept": "application/json", "Content-Type": "application/json", "access-token": self.token})
            with urllib.request.urlopen(req, timeout=30) as r:
                bars += dhan_bars(json.load(r), minutes)
        return bars


class UpstoxSource:
    name = "upstox"

    def __init__(self):
        self.token = _require("UPSTOX_ACCESS_TOKEN")

    def history(self, isin: str, start: date, end: date, minutes: int = 5) -> list:
        key = urllib.parse.quote("NSE_EQ|%s" % isin, safe="")
        bars = []
        for a, b in _windows(start, end, 28):
            req = urllib.request.Request(UPSTOX_CANDLES % (key, minutes, b, a), headers={
                "Accept": "application/json", "Authorization": "Bearer " + self.token})
            with urllib.request.urlopen(req, timeout=30) as r:
                bars += upstox_bars(json.load(r), minutes)
        return bars


def dhan_security_ids(symbols: list) -> dict:
    """{NSE symbol: Dhan security id}, from Dhan's public scrip master."""
    with urllib.request.urlopen(urllib.request.Request(DHAN_SCRIPS, headers={"User-Agent": "nse-algo-trader"}), timeout=60) as r:
        text = r.read().decode("utf-8", "replace")
    wanted, out = set(symbols), {}
    for row in csv.DictReader(io.StringIO(text)):
        if row.get("SEM_EXM_EXCH_ID") == "NSE" and row.get("SEM_INSTRUMENT_NAME") == "EQUITY" and row.get("SEM_SERIES") == "EQ":
            if row.get("SEM_TRADING_SYMBOL") in wanted:
                out[row["SEM_TRADING_SYMBOL"]] = row["SEM_SMST_SECURITY_ID"]
    return out


# ---- Dhan live feed: binary, little-endian. See dhanhq.co/docs/v2/live-market-feed ----------------
SUBSCRIBE_QUOTE = 17
NIFTY_50_ID = "13"
DISCONNECT = 50


def subscribe_messages(security_ids: list, code: int = SUBSCRIBE_QUOTE, index_ids: tuple = ()) -> list:
    """At most 100 instruments a message, per Dhan's limit. Indices use their own segment."""
    items = [{"ExchangeSegment": "NSE_EQ", "SecurityId": str(s)} for s in security_ids]
    items += [{"ExchangeSegment": "IDX_I", "SecurityId": str(s)} for s in index_ids]
    return [json.dumps({"RequestCode": code, "InstrumentCount": len(items[k:k + 100]), "InstrumentList": items[k:k + 100]})
            for k in range(0, len(items), 100)]


def parse_packet(data: bytes):
    """-> dict for a Ticker (2) or Quote (4) packet, {"disconnect": code} for 50, else None."""
    if len(data) < 8:
        return None
    code, _, _, sid = struct.unpack_from("<BHBi", data, 0)
    if code == DISCONNECT and len(data) >= 10:
        return {"disconnect": struct.unpack_from("<h", data, 8)[0]}
    if code == 2 and len(data) >= 16:
        ltp, ltt = struct.unpack_from("<fi", data, 8)
        return {"security_id": str(sid), "ltp": ltp, "ts": ltt, "volume": None}
    if code == 4 and len(data) >= 50:
        ltp, _, ltt, _, volume = struct.unpack_from("<fhifi", data, 8)
        return {"security_id": str(sid), "ltp": ltp, "ts": ltt, "volume": volume}
    return None
