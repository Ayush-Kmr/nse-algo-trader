"""Event-driven backtest: replays history bar by bar through the SAME Engine used for paper trading.

Every figure is net of the cost model. Days are split chronologically: the first part is in-sample,
the last part is out-of-sample. Nothing is tuned on the out-of-sample days.
"""
from __future__ import annotations

import copy
import re
import statistics
from datetime import datetime, timedelta

from .data import by_day
from .engine import Engine, new_state
from .models import slip_pct
from .timeutil import hhmm


def run(cfg: dict, history: dict, index_symbol: str, exclude_date=None) -> dict:
    """history: {symbol: [Bar, ...]} across many days, index included under index_symbol."""
    days_by_sym = {s: by_day(b) for s, b in history.items()}
    all_days = sorted({d for m in days_by_sym.values() for d in m})
    if exclude_date is not None:
        all_days = [d for d in all_days if d != exclude_date]

    state = new_state(cfg)
    eng = Engine(cfg, state)
    trades, events, daily = [], [], []
    open_t = hhmm(cfg["session_open"])
    sq = hhmm(cfg["square_off"])

    for d in all_days:
        day = {s: m.get(d, []) for s, m in days_by_sym.items()}
        day = {s: [b for b in bars if b.ts.time() >= open_t] for s, bars in day.items()}
        stamps = sorted({b.ts for bars in day.values() for b in bars})
        if not stamps:
            continue
        idx = {s: 0 for s in day}
        last_now = None
        for ts in stamps:
            now = ts + timedelta(minutes=cfg["bar_minutes"])
            view = {}
            for s, bars in day.items():
                i = idx[s]
                while i < len(bars) and bars[i].ts <= ts:
                    i += 1
                idx[s] = i
                view[s] = bars[:i]
            index_bars = view.pop(index_symbol, None)
            for ev in eng.step(now, view, index_bars):
                events.append(dict(ev, date=d.isoformat()))
            last_now = now
            if now.time() > sq and not state["positions"]:
                break
        if state["positions"]:  # data ended early: flatten at the last price we saw
            eng.step(datetime.combine(d, sq, last_now.tzinfo) if last_now.time() < sq else last_now,
                     {s: day[s] for s in day if s != index_symbol}, day.get(index_symbol))
        t = state["today"]
        trades.extend(dict(tr, date=d.isoformat()) for tr in t["trades"])
        daily.append({"date": d.isoformat(), "net": round(t["realised"], 2), "trades": len(t["trades"])})

    return {"trades": trades, "events": events, "daily": daily, "days": [d.isoformat() for d in all_days],
            "final_equity": state["equity"]}


def metrics(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    net = [t["net_pnl"] for t in trades]
    gross = [t["gross_pnl"] for t in trades]
    wins = [x for x in net if x > 0]
    losses = [x for x in net if x <= 0]
    rs = [t["r_multiple"] for t in trades]
    eq, peak, mdd = 0.0, 0.0, 0.0
    for x in net:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    return {
        "trades": n,
        "win_rate_pct": round(100 * len(wins) / n, 1),
        "net_total": round(sum(net), 2),
        "gross_total": round(sum(gross), 2),
        "charges_total": round(sum(t["charges"] for t in trades), 2),
        "expectancy_rs": round(sum(net) / n, 2),
        "avg_r_net": round(sum(rs) / n, 3),
        "avg_r_se": round(statistics.stdev(rs) / n ** 0.5, 4) if n > 1 else None,
        "profit_factor": round(sum(wins) / -sum(losses), 2) if losses and sum(losses) < 0 else None,
        "max_drawdown_rs": round(mdd, 2),
        "exits": _count(t["exit_reason"] for t in trades),
    }


def _count(xs) -> dict:
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return out


def split_report(result: dict, oos_fraction: float = 0.3, tests: int = 1) -> dict:
    days = result["days"]
    cut = days[int(len(days) * (1 - oos_fraction))] if days else None
    ins = [t for t in result["trades"] if cut is None or t["date"] < cut]
    oos = [t for t in result["trades"] if cut is not None and t["date"] >= cut]
    by_strat = {}
    for t in result["trades"]:
        by_strat.setdefault(t["strategy"], []).append(t)
    rep = {
        "days": len(days), "first_day": days[0] if days else None, "last_day": days[-1] if days else None,
        "oos_from": cut,
        "all": metrics(result["trades"]),
        "in_sample": metrics(ins),
        "out_of_sample": metrics(oos),
        "by_strategy": {k: metrics(v) for k, v in sorted(by_strat.items())},
        "blocks": _count(re.sub(r"\d+(\.\d+)?", "N", r.strip())
                         for e in result["events"] if e["kind"] == "BLOCK"
                         for r in e["msg"].split(": ", 1)[-1].split(";")),
    }
    rep["verdict"] = verdict(rep["out_of_sample"], tests)
    return rep


def verdict(oos: dict, tests: int = 1) -> str:
    """A positive average is not enough on 30 trades: the 95% lower bound on avg R must clear zero.

    `tests` is how many variants were tried on this data (Bonferroni), so a lucky one cannot pass.
    """
    n = oos.get("trades", 0)
    if n < 30:
        return "INCONCLUSIVE: %d out-of-sample trades, need 30+ before any conclusion." % n
    if oos["expectancy_rs"] <= 0:
        return "FAILS the gate: out-of-sample expectancy is %.2f per trade after costs." % oos["expectancy_rs"]
    low = oos["avg_r_net"] - statistics.NormalDist().inv_cdf(1 - 0.025 / tests) * oos["avg_r_se"]
    if low <= 0:
        return "INCONCLUSIVE: avg %+.3fR is positive but its lower bound is %+.3fR (%d test(s))." % (
            oos["avg_r_net"], low, tests)
    return ("PASSES the first gate (out-of-sample avg R lower bound %+.3fR after costs). "
            "Next gate: 30+ sessions of forward paper trading." % low)


def to_markdown(rep: dict, cfg: dict) -> str:
    L = ["# Backtest report", "",
         "Data: %s to %s (%d sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **%s**." % (
             rep["first_day"], rep["last_day"], rep["days"], rep["oos_from"]),
         "Strategies: %s. Capital %s, risk %s%%/trade, daily limit %s%%. All figures **net** of Angel One charges and %s%% per fill (slippage + half spread)." % (
             ", ".join(cfg["strategies"]), cfg["capital"], cfg["risk_per_trade_pct"], cfg["daily_loss_limit_pct"], round(slip_pct(cfg), 4)),
         "", "**Verdict: %s**" % rep["verdict"], "",
         "| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    rows = [("all", rep["all"]), ("in-sample", rep["in_sample"]), ("out-of-sample", rep["out_of_sample"])]
    rows += [("strategy: " + k, v) for k, v in rep["by_strategy"].items()]
    for name, m in rows:
        if not m.get("trades"):
            L.append("| %s | 0 | | | | | | | | |" % name)
            continue
        L.append("| %s | %d | %.1f | %.2f | %.2f | %.2f | %.2f | %.3f | %s | %.2f |" % (
            name, m["trades"], m["win_rate_pct"], m["net_total"], m["gross_total"], m["charges_total"],
            m["expectancy_rs"], m["avg_r_net"], m["profit_factor"] if m["profit_factor"] is not None else "-",
            m["max_drawdown_rs"]))
    if rep["all"].get("trades"):
        L += ["", "Exits: " + ", ".join("%s %d" % kv for kv in rep["all"]["exits"].items())]
    if rep["blocks"]:
        L += ["", "Top reasons the risk engine blocked a signal:", ""]
        for reason, n in sorted(rep["blocks"].items(), key=lambda kv: -kv[1])[:8]:
            L.append("- %s: %d" % (reason.strip(), n))
    L += ["", "60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.", ""]
    return "\n".join(L)


def clone_cfg(cfg: dict, **overrides) -> dict:
    c = copy.deepcopy(cfg)
    c.update(overrides)
    return c
