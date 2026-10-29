"""The trading loop, one step at a time. The same code runs live paper ticks and the backtest.

step() is given the clock and today's completed bars; it manages exits first, then looks for entries.
All state lives in a plain dict so it can be saved between GitHub Actions runs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from .broker.paper import PaperBroker
from .costs import CostModel
from .models import Position
from .risk import Account, check_entry
from .strategies import REGISTRY
from .timeutil import hhmm


def new_state(cfg: dict) -> dict:
    return {"version": 1, "date": None, "equity": float(cfg["capital"]), "positions": {},
            "today": _blank_day(), "history": {}}


def _blank_day() -> dict:
    return {"trades": [], "realised": 0.0, "entries": 0, "symbols": [], "seen": [], "events": [], "flags": []}


class Engine:
    def __init__(self, cfg: dict, state: dict, notify: Optional[Callable[[dict], None]] = None):
        self.cfg = cfg
        self.state = state
        self.costs = CostModel(cfg["costs"])
        self.broker = PaperBroker(self.costs, cfg["slippage_pct"], cfg["tick_size"])
        self.notify = notify or (lambda ev: None)
        self.strategies = [(n, REGISTRY[n]) for n in cfg["strategies"]]

    # ---- bookkeeping -------------------------------------------------------------------------
    def _event(self, now: datetime, kind: str, symbol: str, msg: str, **data) -> dict:
        ev = {"time": now.strftime("%H:%M"), "kind": kind, "symbol": symbol, "msg": msg}
        if data:
            ev["data"] = data
        self.state["today"]["events"].append(ev)
        self._new_events.append(ev)
        if kind in ("ENTRY", "EXIT", "CRITICAL"):
            self.notify(ev)
        return ev

    def _once(self, flag: str) -> bool:
        flags = self.state["today"]["flags"]
        if flag in flags:
            return False
        flags.append(flag)
        return True

    def roll_day(self, now: datetime) -> None:
        d = now.date().isoformat()
        if self.state["date"] == d:
            return
        prev = self.state["date"]
        if prev and prev not in self.state["history"]:
            t = self.state["today"]
            self.state["history"][prev] = {"net": round(t["realised"], 2), "trades": len(t["trades"])}
        self.state["date"] = d
        self.state["today"] = _blank_day()
        if self.state["positions"]:
            self.state["today"]["flags"].append("carried")
            self._event(now, "CRITICAL", "*", "positions carried overnight: squaring off at first price",
                        symbols=sorted(self.state["positions"]))

    def account(self, kill_switch: bool) -> Account:
        pos = [Position.from_dict(p) for p in self.state["positions"].values()]
        open_value = sum(p.qty * p.entry_price for p in pos)
        t = self.state["today"]
        return Account(
            equity=self.state["equity"],
            cash_available=self.state["equity"] - open_value,
            open_positions=len(pos),
            open_risk=sum(p.planned_risk for p in pos),
            trades_today=t["entries"],
            realised_today=t["realised"],
            symbols_today=set(t["symbols"]),
            kill_switch=kill_switch,
        )

    # ---- exits -------------------------------------------------------------------------------
    def _close(self, now, pos: Position, price: float, reason: str) -> None:
        tr = self.broker.close(pos, price, reason, now)
        t = self.state["today"]
        t["trades"].append(tr.to_dict())
        t["realised"] = round(t["realised"] + tr.net_pnl, 2)
        self.state["equity"] = round(self.state["equity"] + tr.net_pnl, 2)
        self.state["positions"].pop(pos.symbol, None)
        self._event(now, "EXIT", pos.symbol, "%s %d @ %.2f, net %+.2f (%+.2fR, charges %.2f)" % (
            reason, pos.qty, price, tr.net_pnl, tr.r_multiple, tr.charges), trade=tr.to_dict())

    def _manage(self, now, pos: Position, bars: list) -> None:
        last = datetime.fromisoformat(pos.last_bar_ts)
        for b in bars:
            if b.ts <= last:
                continue
            pos.last_bar_ts = b.ts.isoformat()
            hit = self.broker.check_bar(pos, b)
            if hit:
                self._close(b.end, pos, *hit)
                return
            self.broker.update_stop(pos, b, self.cfg.get("exits", {}))
        self.state["positions"][pos.symbol] = pos.to_dict()

        must_flatten = now.time() >= hhmm(self.cfg["square_off"]) or "carried" in self.state["today"]["flags"]
        if must_flatten and pos.symbol in self.state["positions"]:
            if bars:
                self._close(now, pos, self.broker.square_off_price(bars[-1].close), "square-off")
            elif self._once("noprice:" + pos.symbol):
                self._event(now, "CRITICAL", pos.symbol, "square-off due but no price available")

    # ---- the step ----------------------------------------------------------------------------
    def step(self, now: datetime, bars_by_symbol: dict, index_bars: Optional[list],
             kill_switch: bool = False) -> list:
        self._new_events = []
        self.roll_day(now)
        cfg = self.cfg

        for sym, pd in list(self.state["positions"].items()):
            bars = bars_by_symbol.get(sym)
            if bars is None:
                if self._once("nodata:%s:%s" % (sym, now.strftime("%H:%M"))):
                    self._event(now, "WARN", sym, "no data this tick for an open position")
                continue
            self._manage(now, Position.from_dict(pd), bars)

        if kill_switch:
            if self._once("kill"):
                self._event(now, "KILL", "*", "kill switch on: no new entries (open positions still managed)")
            return self._new_events

        start, end = (hhmm(t) for t in cfg["entry_window"])
        if not (start <= now.time() <= end):
            return self._new_events

        if cfg["regime"].get("require_green_day"):
            if not index_bars:
                if self._once("regime-unknown"):
                    self._event(now, "INFO", cfg["regime"]["index"], "index data missing: no entries (fail closed)")
                return self._new_events
            if index_bars[-1].close <= index_bars[0].open:
                if self._once("regime-red:" + now.strftime("%H")):
                    self._event(now, "INFO", cfg["regime"]["index"], "index below its open: longs paused")
                return self._new_events

        today = self.state["today"]
        idx_chg = _pct_from_open(index_bars)
        min_rs = cfg.get("filters", {}).get("min_rs_pct")

        # Collect every fresh signal first, then take the strongest relative to the index.
        candidates = []
        for sym in cfg["universe"]:
            if sym in self.state["positions"] or sym in today["symbols"]:
                continue
            bars = bars_by_symbol.get(sym) or []
            for name, fn in self.strategies:
                sig = fn(sym, bars, cfg)
                if not sig:
                    continue
                key = "%s|%s" % (sym, name)
                if key in today["seen"]:
                    continue
                today["seen"].append(key)
                age = sum(1 for b in bars if b.ts > sig.bar_ts)
                if age > cfg["max_signal_age_bars"]:
                    self._event(now, "EXPIRED", sym, "%s signal from %s is %d bars old" % (
                        name, sig.bar_ts.strftime("%H:%M"), age))
                    continue
                rs = _pct_from_open(bars) - idx_chg if idx_chg is not None else 0.0
                if min_rs is not None and rs < min_rs:
                    self._event(now, "FILTER", sym, "%s: %.2f%% vs index, below %.2f%%" % (name, rs, min_rs))
                    continue
                candidates.append((rs, sym, name, sig, bars))
                break

        for rs, sym, name, sig, bars in sorted(candidates, key=lambda c: -c[0]):
            v = check_entry(sig, self.account(kill_switch), cfg, self.costs, now)
            if not v.ok:
                self._event(now, "BLOCK", sym, "%s: %s" % (name, "; ".join(v.reasons)),
                            signal=_sig_dict(sig), **v.details)
                continue
            pos = self.broker.open(sig, v.qty, v.details["loss_at_stop"])
            self.state["positions"][sym] = pos.to_dict()
            today["entries"] += 1
            today["symbols"].append(sym)
            self._event(now, "ENTRY", sym, "%s: buy %d @ %.2f, stop %.2f, target %.2f, risk %.2f, RS %+.2f%% (%s)" % (
                name, v.qty, pos.entry_price, pos.stop, pos.target, pos.planned_risk, rs, sig.reason),
                signal=_sig_dict(sig), **v.details)
            self._manage(now, pos, bars)  # bars after the signal bar, if this tick ran late
        return self._new_events


def _pct_from_open(bars) -> Optional[float]:
    if not bars or bars[0].open <= 0:
        return None
    return (bars[-1].close - bars[0].open) / bars[0].open * 100


def _sig_dict(sig) -> dict:
    return {"entry": sig.entry, "stop": sig.stop, "target": sig.target, "bar": sig.bar_ts.strftime("%H:%M")}
