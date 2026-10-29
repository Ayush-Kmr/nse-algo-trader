from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta


@dataclass
class Bar:
    ts: datetime  # bar START, IST-aware
    open: float
    high: float
    low: float
    close: float
    volume: float
    minutes: int = 5

    @property
    def end(self) -> datetime:
        return self.ts + timedelta(minutes=self.minutes)


@dataclass
class Signal:
    symbol: str
    strategy: str
    entry: float
    stop: float
    target: float
    bar_ts: datetime
    reason: str


@dataclass
class Position:
    symbol: str
    strategy: str
    qty: int
    entry_price: float
    stop: float
    target: float
    entry_ts: str
    planned_risk: float  # rupees lost at the stop, costs included
    last_bar_ts: str
    initial_stop: float = 0.0  # the stop at entry; `stop` may trail up from here
    peak: float = 0.0          # highest high since entry

    def __post_init__(self):
        self.initial_stop = self.initial_stop or self.stop
        self.peak = self.peak or self.entry_price

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Position":
        return cls(**d)


@dataclass
class Trade:
    symbol: str
    strategy: str
    qty: int
    entry_price: float
    exit_price: float
    entry_ts: str
    exit_ts: str
    exit_reason: str
    gross_pnl: float
    charges: float
    net_pnl: float
    planned_risk: float
    r_multiple: float

    def to_dict(self) -> dict:
        return asdict(self)


def round_tick(price: float, tick: float, mode: str = "nearest") -> float:
    """Snap a price to the exchange tick. The epsilon stops 100.05/0.05 = 2000.9999 from flooring wrong."""
    n = price / tick
    if mode == "down":
        n = math.floor(n + 1e-9)
    elif mode == "up":
        n = math.ceil(n - 1e-9)
    else:
        n = round(n)
    return round(n * tick, 2)
