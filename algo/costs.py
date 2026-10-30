"""Angel One intraday equity charges (NSE). Every P&L and every size in this repo goes through here.

Rates live in config.json -> costs, flagged `verified: false` until checked against the broker's
live charge sheet.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal


def _d(x) -> Decimal:
    return Decimal(str(x))


def _paise(x: Decimal) -> float:
    return float(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass
class Charges:
    brokerage: float
    stt: float
    exchange: float
    sebi: float
    stamp: float
    gst: float
    total: float

    def to_dict(self) -> dict:
        return asdict(self)


class CostModel:
    def __init__(self, rates: dict):
        self.flat = _d(rates["brokerage_flat"])
        self.brk_min = _d(rates.get("brokerage_min", 0))
        self.brk_pct = _d(rates["brokerage_pct"]) / 100
        self.stt_sell = _d(rates["stt_sell_pct"]) / 100
        self.exch = _d(rates["exchange_pct"]) / 100
        self.sebi = _d(rates["sebi_per_crore"]) / _d(10_000_000)
        self.stamp_buy = _d(rates["stamp_buy_pct"]) / 100
        self.gst = _d(rates["gst_pct"]) / 100

    def brokerage(self, order_value) -> Decimal:
        """Per executed order: the flat fee or the percentage, whichever is lower, with a minimum."""
        v = _d(order_value)
        if v <= 0:
            return Decimal(0)
        return max(self.brk_min, min(self.flat, v * self.brk_pct))

    def round_trip(self, buy_value, sell_value) -> Charges:
        buy, sell = _d(buy_value), _d(sell_value)
        turnover = buy + sell
        brk = self.brokerage(buy) + self.brokerage(sell)
        stt = sell * self.stt_sell
        exch = turnover * self.exch
        sebi = turnover * self.sebi
        stamp = buy * self.stamp_buy
        gst = (brk + exch + sebi) * self.gst
        total = brk + stt + exch + sebi + stamp + gst
        return Charges(_paise(brk), _paise(stt), _paise(exch), _paise(sebi),
                       _paise(stamp), _paise(gst), _paise(total))
