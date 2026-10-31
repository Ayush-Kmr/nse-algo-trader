"""Real-time paper trading from the Dhan WebSocket feed. PAPER only: this file cannot place an order.

Ticks build 5-minute bars. Every finished bar runs the same Engine as the backtest. Stops are also
checked on every tick. If ticks stop, entries stop and the channel is told. Run it on an always-on
machine: GitHub Actions cannot hold a socket open all day. Needs `pip install -r requirements-live.txt`.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta

from . import feeds
from .chart import chart_notifier
from .engine import Engine
from .models import Bar, Position
from .notify import telegram
from .timeutil import IST, hhmm


class BarBuilder:
    """Ticks -> 5-minute bars. A bar is finished when a later tick arrives; nothing is ever filled in."""

    def __init__(self, minutes: int = 5):
        self.minutes = minutes
        self.current, self.done, self.day_volume = {}, {}, {}

    def slot(self, ts: datetime) -> datetime:
        return ts.replace(minute=ts.minute - (ts.minute - 15) % self.minutes if ts.minute >= 15 or ts.hour > 9 else ts.minute,
                          second=0, microsecond=0)

    def add(self, sym: str, price: float, ts: datetime, volume=None):
        """-> the finished Bar if this tick closed one, else None."""
        start = self.slot(ts)
        traded = 0.0
        if volume is not None:
            traded = max(0.0, volume - self.day_volume.get(sym, 0))
            self.day_volume[sym] = max(volume, self.day_volume.get(sym, 0))
        cur = self.current.get(sym)
        if cur is None or cur.ts != start:
            finished = cur
            self.current[sym] = Bar(start, price, price, price, price, traded, self.minutes)
            if finished:
                self.done.setdefault(sym, []).append(finished)
            return finished
        cur.high, cur.low, cur.close = max(cur.high, price), min(cur.low, price), price
        cur.volume += traded
        return None


class PaperLive:
    def __init__(self, cfg: dict, state: dict, ids: dict, save, kill_file: str, stale_seconds: int = 60):
        if cfg.get("mode") not in ("READ_ONLY", "PAPER"):
            raise RuntimeError("live feed runs in PAPER or READ_ONLY only")
        self.cfg, self.state, self.save, self.kill_file, self.stale_seconds = cfg, state, save, kill_file, stale_seconds
        self.by_id = {str(v): k for k, v in ids.items()}
        self.builder = BarBuilder(cfg["bar_minutes"])
        self.last_tick, self.stale = None, False
        self.index = cfg["regime"]["index"]

    def killed(self) -> bool:
        return os.path.exists(self.kill_file) or os.environ.get("KILL_SWITCH", "") in ("1", "true", "on", "yes")

    def engine(self) -> Engine:
        return Engine(self.cfg, self.state, notify=chart_notifier(self.builder.done))

    def on_packet(self, p: dict) -> None:
        sym = self.by_id.get(p.get("security_id"))
        if not sym or not p.get("ltp") or p["ltp"] <= 0:
            return  # a bad tick is dropped, never repaired
        ts = datetime.fromtimestamp(p["ts"], IST)
        self.last_tick = ts
        if self.stale:
            self.stale = False
            telegram("✅ [PAPER] market feed recovered")
        self.check_stop(sym, p["ltp"], ts)
        finished = self.builder.add(sym, p["ltp"], ts, p.get("volume"))
        if finished:
            self.on_bar(finished.end)

    def check_stop(self, sym: str, price: float, ts: datetime) -> None:
        d = self.state["positions"].get(sym)
        if d:
            pos = Position.from_dict(d)
            if price <= pos.stop:
                eng = self.engine()
                eng._new_events = []
                eng._close(ts, pos, eng.broker.square_off_price(price), "stop")
                self.save(self.state)

    def on_bar(self, end: datetime) -> None:
        bars = {s: b for s, b in self.builder.done.items() if s != self.index}
        eng = self.engine()
        eng.step(end, bars, self.builder.done.get(self.index), kill_switch=self.killed(), live=True)
        self.save(self.state)

    def check_stale(self, now: datetime) -> bool:
        in_session = hhmm(self.cfg["session_open"]) <= now.time() < hhmm(self.cfg["session_close"])
        late = self.last_tick is not None and (now - self.last_tick) > timedelta(seconds=self.stale_seconds)
        if in_session and late and not self.stale:
            self.stale = True
            telegram("🚨 [PAPER] no market data for %d seconds: open paper positions are not being watched" % self.stale_seconds)
        return self.stale


async def run_dhan(live: PaperLive, ids: list, index_ids: tuple = ()) -> None:
    import websockets  # optional dependency: only this live path needs it

    url = feeds.DHAN_WS % (feeds._require("DHAN_ACCESS_TOKEN"), feeds._require("DHAN_CLIENT_ID"))
    delay = 1
    while True:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                for msg in feeds.subscribe_messages(ids, index_ids=index_ids):
                    await ws.send(msg)
                delay = 1
                async for raw in ws:
                    if isinstance(raw, bytes):
                        p = feeds.parse_packet(raw)
                        if p and "disconnect" in p:
                            telegram("🚨 [PAPER] Dhan feed disconnected, code %s" % p["disconnect"])
                        elif p:
                            live.on_packet(p)
        except Exception as e:  # noqa: BLE001 - reconnect; never die silently during market hours
            telegram("⚠️ [PAPER] feed connection lost (%s), reconnecting" % type(e).__name__)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 60)


def state_saver(path: str):
    def save(state: dict) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(state, fh)
        os.replace(tmp, path)
    return save
