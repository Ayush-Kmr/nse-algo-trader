"""Paper broker. Simulates fills conservatively on completed bars.

- Entry: limit at the signal price plus slippage.
- Stop and target both touched in one bar: the STOP is assumed to fill first.
- A gap through the stop fills at the bar's open, not at the stop.
- Every round trip is charged through the cost model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from ..costs import CostModel
from ..models import Bar, Position, Signal, Trade, round_tick
from .base import Broker


class PaperBroker(Broker):
    def __init__(self, costs: CostModel, slippage_pct: float, tick: float):
        self.costs = costs
        self.slip = slippage_pct / 100
        self.tick = tick

    def open(self, sig: Signal, qty: int, planned_risk: float) -> Position:
        fill = round_tick(sig.entry * (1 + self.slip), self.tick, "up")
        ts = sig.bar_ts.isoformat()
        return Position(sig.symbol, sig.strategy, qty, fill, sig.stop, sig.target, ts, planned_risk, ts)

    def check_bar(self, pos: Position, bar: Bar) -> Optional[Tuple[float, str]]:
        sell = lambda px: round_tick(px * (1 - self.slip), self.tick, "down")
        kind = "trail stop" if pos.stop > pos.initial_stop else "stop"
        if bar.open <= pos.stop:
            return sell(bar.open), kind + " (gap)"
        if bar.low <= pos.stop:
            return sell(pos.stop), kind
        if bar.open >= pos.target:
            return bar.open, "target (gap)"
        if bar.high >= pos.target:
            return pos.target, "target"
        return None

    def update_stop(self, pos: Position, bar: Bar, rules: dict) -> None:
        """After a completed bar with no exit: ratchet the stop up, never down. Applies from the next bar."""
        pos.peak = max(pos.peak, bar.high)
        r0 = pos.entry_price - pos.initial_stop
        if r0 <= 0:
            return
        be = rules.get("breakeven_at_r")
        if be and pos.peak >= pos.entry_price + be * r0:
            pos.stop = max(pos.stop, round_tick(pos.entry_price, self.tick, "up"))
        ts = rules.get("trail_start_r")
        if ts and pos.peak >= pos.entry_price + ts * r0:
            trail = round_tick(pos.peak - rules.get("trail_r", 1.0) * r0, self.tick, "down")
            pos.stop = max(pos.stop, trail)

    def square_off_price(self, last_price: float) -> float:
        # Market orders are banned for algos: this models a marketable limit a few ticks through.
        return round_tick(last_price * (1 - self.slip), self.tick, "down")

    def close(self, pos: Position, price: float, reason: str, ts: datetime) -> Trade:
        buy_v, sell_v = pos.qty * pos.entry_price, pos.qty * price
        gross = sell_v - buy_v
        ch = self.costs.round_trip(buy_v, sell_v).total
        net = gross - ch
        r = net / pos.planned_risk if pos.planned_risk > 0 else 0.0
        return Trade(pos.symbol, pos.strategy, pos.qty, pos.entry_price, price, pos.entry_ts,
                     ts.isoformat(), reason, round(gross, 2), ch, round(net, 2), pos.planned_risk, round(r, 3))
