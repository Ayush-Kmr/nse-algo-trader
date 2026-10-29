"""Position sizing with costs and slippage inside the risk, not added afterwards."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .costs import CostModel


@dataclass
class Size:
    qty: int
    buy_px: float
    loss_at_stop: float     # rupees, slippage + charges included
    charges_at_stop: float
    limited_by: str


def loss_at_stop(qty: int, buy_px: float, sell_px: float, costs: CostModel):
    ch = costs.round_trip(qty * buy_px, qty * sell_px)
    return qty * (buy_px - sell_px) + ch.total, ch.total


def size_position(entry: float, stop: float, risk_budget: float, costs: CostModel,
                  slippage_pct: float, max_value: float) -> Size:
    slip = slippage_pct / 100
    buy_px = entry * (1 + slip)
    sell_px = stop * (1 - slip)
    per_share = buy_px - sell_px
    if per_share <= 0 or risk_budget <= 0:
        return Size(0, buy_px, 0.0, 0.0, "invalid stop")

    by_risk = math.floor(risk_budget / per_share)
    by_value = math.floor(max_value / buy_px) if max_value > 0 else 0
    qty, limited_by = (by_risk, "max loss per trade") if by_risk <= by_value else (by_value, "position cap / cash")

    # Charges are not linear in qty (flat brokerage), so step down until the all-in loss fits.
    while qty > 0:
        loss, ch = loss_at_stop(qty, buy_px, sell_px, costs)
        if loss <= risk_budget:
            return Size(qty, buy_px, round(loss, 2), ch, limited_by)
        qty -= 1
        limited_by = "max loss per trade (after costs)"
    return Size(0, buy_px, 0.0, 0.0, "stop too far for the risk budget")
