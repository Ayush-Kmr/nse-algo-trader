"""Risk engine. Pure and deterministic: no network, no LLM, no clock of its own.

A BLOCK is final. Exits never come through here: getting out is never blocked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .costs import CostModel
from .models import Signal
from .sizing import size_position
from .timeutil import hhmm


@dataclass
class Account:
    equity: float
    cash_available: float
    open_positions: int
    open_risk: float           # rupees at risk across open positions
    trades_today: int
    realised_today: float      # net, negative = loss
    symbols_today: set = field(default_factory=set)
    kill_switch: bool = False


@dataclass
class Verdict:
    ok: bool
    reasons: list
    qty: int = 0
    details: dict = field(default_factory=dict)


def check_entry(sig: Signal, acct: Account, cfg: dict, costs: CostModel, now: datetime) -> Verdict:
    reasons = []

    if cfg.get("mode") == "READ_ONLY":
        reasons.append("mode is READ_ONLY")
    if acct.kill_switch:
        reasons.append("kill switch is on")

    start, end = (hhmm(t) for t in cfg["entry_window"])
    if not (start <= now.time() <= end):
        reasons.append("outside entry window %s-%s" % tuple(cfg["entry_window"]))

    if sig.symbol in acct.symbols_today:
        reasons.append("already traded %s today" % sig.symbol)
    if acct.open_positions >= cfg["max_open_positions"]:
        reasons.append("max open positions (%d) reached" % cfg["max_open_positions"])
    if acct.trades_today >= cfg["max_trades_per_day"]:
        reasons.append("max trades per day (%d) reached" % cfg["max_trades_per_day"])

    if not (sig.stop < sig.entry < sig.target):
        reasons.append("bad geometry: need stop < entry < target (long only)")
        return Verdict(False, reasons)

    risk_budget = acct.equity * cfg["risk_per_trade_pct"] / 100
    daily_limit = acct.equity * cfg["daily_loss_limit_pct"] / 100
    losses_so_far = max(0.0, -acct.realised_today)
    room_today = daily_limit - losses_so_far - acct.open_risk
    budget = min(risk_budget, room_today)
    if budget <= 0:
        reasons.append("daily loss limit: no room left (lost %.2f, open risk %.2f, limit %.2f)"
                       % (losses_so_far, acct.open_risk, daily_limit))
        return Verdict(False, reasons)

    max_value = min(acct.equity * cfg["max_position_pct"] / 100, acct.cash_available)
    size = size_position(sig.entry, sig.stop, budget, costs, cfg["slippage_pct"], max_value)
    if size.qty < 1:
        reasons.append("size is zero: %s" % size.limited_by)
        return Verdict(False, reasons)

    qty = size.qty
    target_ch = costs.round_trip(qty * size.buy_px, qty * sig.target).total
    net_reward = qty * (sig.target - size.buy_px) - target_ch
    net_rr = net_reward / size.loss_at_stop if size.loss_at_stop > 0 else 0.0
    cost_to_risk = 100 * size.charges_at_stop / risk_budget

    if net_rr < cfg["min_net_reward_risk"]:
        reasons.append("net reward:risk %.2f below %.2f" % (net_rr, cfg["min_net_reward_risk"]))
    if cost_to_risk > cfg["max_cost_to_risk_pct"]:
        reasons.append("charges are %.0f%% of the risk budget (max %s%%)" % (cost_to_risk, cfg["max_cost_to_risk_pct"]))

    details = {
        "qty": qty,
        "position_value": round(qty * size.buy_px, 2),
        "loss_at_stop": size.loss_at_stop,
        "charges_at_stop": size.charges_at_stop,
        "net_reward_at_target": round(net_reward, 2),
        "net_rr": round(net_rr, 2),
        "cost_to_risk_pct": round(cost_to_risk, 1),
        "limited_by": size.limited_by,
    }
    return Verdict(not reasons, reasons, qty if not reasons else 0, details)
