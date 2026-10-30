"""Research that the portfolio backtest cannot do.

signal_study: every signal on its own, with no position limits or risk blocks. The backtest takes
about 1 signal in 10, so this gets far more evidence from the same bars. It answers "do these entries
move?", not "what would the account have made?".

walk_forward: pick the best variant on a training window, trade it on the next unseen window, roll
on. Only the unseen windows are scored, so choosing a variant cannot flatter the result.
"""
from __future__ import annotations

import statistics
from datetime import timedelta

from . import backtest as bt
from .broker.paper import PaperBroker
from .costs import CostModel
from .data import by_day
from .experiments import deep_merge
from .models import slip_pct
from .sizing import size_position
from .strategies import REGISTRY
from .timeutil import hhmm


def _walk(sig, bars, cfg, broker, costs):
    """One signal to its exit under the engine's fill rules. -> trade dict, or None if unsizable."""
    equity = cfg["capital"]
    size = size_position(sig.entry, sig.stop, equity * cfg["risk_per_trade_pct"] / 100, costs, slip_pct(cfg),
                         equity * cfg["max_position_pct"] / 100)
    if size.qty < 1:
        return None
    pos = broker.open(sig, size.qty, size.loss_at_stop)
    square_off = hhmm(cfg["square_off"])
    last = None
    for b in bars:
        if b.ts <= sig.bar_ts:
            continue
        last = b
        hit = broker.check_bar(pos, b)
        if hit:
            return broker.close(pos, hit[0], hit[1], b.end).to_dict()
        broker.update_stop(pos, b, cfg.get("exits", {}))
        if b.end.time() >= square_off:
            break
    if last is None:
        return None
    return broker.close(pos, broker.square_off_price(last.close), "square-off", last.end).to_dict()


def _green(index_bars, ts) -> bool:
    seen = [b for b in index_bars if b.ts <= ts]
    return bool(seen) and seen[-1].close > seen[0].open


def signal_rows(cfg: dict, history: dict, exclude_date=None) -> list:
    index = cfg["regime"]["index"]
    costs = CostModel(cfg["costs"])
    broker = PaperBroker(costs, slip_pct(cfg), cfg["tick_size"])
    days_by_sym = {s: by_day(b) for s, b in history.items()}
    idx_days = days_by_sym.get(index, {})
    start, end = (hhmm(t) for t in cfg["entry_window"])
    open_t = hhmm(cfg["session_open"])
    rows = []
    for sym in cfg["universe"]:
        for d, bars in sorted(days_by_sym.get(sym, {}).items()):
            if d == exclude_date:
                continue
            bars = [b for b in bars if b.ts.time() >= open_t]
            for name in cfg["strategies"]:
                # A strategy scans forward and returns its first signal, so this sees no future bars.
                sig = REGISTRY[name](sym, bars, cfg)
                if not sig or not (start <= (sig.bar_ts + timedelta(minutes=cfg["bar_minutes"])).time() <= end):
                    continue
                if cfg["regime"].get("require_green_day") and not _green(idx_days.get(d, []), sig.bar_ts):
                    continue
                tr = _walk(sig, bars, cfg, broker, costs)
                if tr:
                    rows.append(dict(tr, date=d.isoformat(), gross_r=tr["gross_pnl"] / tr["planned_risk"],
                                     hour=sig.bar_ts.strftime("%H")))
    return rows


def summarise(rows: list) -> dict:
    n = len(rows)
    if n < 2:
        return {"signals": n}
    gross, net = [r["gross_r"] for r in rows], [r["r_multiple"] for r in rows]
    se = statistics.stdev(gross) / n ** 0.5
    return {"signals": n, "avg_gross_r": round(sum(gross) / n, 3), "gross_se": round(se, 3),
            "gross_low": round(sum(gross) / n - 1.96 * se, 3), "gross_high": round(sum(gross) / n + 1.96 * se, 3),
            "avg_net_r": round(sum(net) / n, 3), "exits": bt._count(r["exit_reason"] for r in rows)}


def signal_study(cfg: dict, history: dict, exclude_date=None, oos_fraction: float = 0.3) -> dict:
    rows = signal_rows(cfg, history, exclude_date)
    days = sorted({r["date"] for r in rows})
    cut = days[int(len(days) * (1 - oos_fraction))] if days else None
    slices = [("all", rows), ("in-sample", [r for r in rows if cut and r["date"] < cut]),
              ("out-of-sample", [r for r in rows if cut and r["date"] >= cut])]
    for key, label in (("strategy", "strategy: "), ("hour", "entry hour: ")):
        for k in sorted({r[key] for r in rows}):
            slices.append((label + k, [r for r in rows if r[key] == k]))
    return {"first_day": days[0] if days else None, "last_day": days[-1] if days else None, "oos_from": cut,
            "slices": [(name, summarise(s)) for name, s in slices]}


def study_markdown(rep: dict) -> str:
    L = ["# Signal study", "",
         "Every signal from %s to %s, with no position limits or risk blocks, sized as a fresh account." % (
             rep["first_day"], rep["last_day"]),
         "Out-of-sample from %s. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R." % rep["oos_from"], "",
         "| slice | signals | avg gross R | 95% interval | avg net R | exits |", "|---|---|---|---|---|---|"]
    for name, m in rep["slices"]:
        if "avg_gross_r" not in m:
            L.append("| %s | %d | | | | |" % (name, m["signals"]))
            continue
        L.append("| %s | %d | %+.3f | %+.3f to %+.3f | %+.3f | %s |" % (
            name, m["signals"], m["avg_gross_r"], m["gross_low"], m["gross_high"], m["avg_net_r"],
            ", ".join("%s %d" % kv for kv in sorted(m["exits"].items()))))
    L += ["", "Hour rows were not pre-registered: read them as leads to retest, never as results.", ""]
    return "\n".join(L)


def walk_forward(cfg: dict, history: dict, variants: list, exclude_date=None, train: int = 30, test: int = 10) -> dict:
    index = cfg["regime"]["index"]
    runs = {v["name"]: bt.run(deep_merge(cfg, v.get("set", {})), history, index, exclude_date) for v in variants}
    days = next(iter(runs.values()))["days"]
    folds, unseen = [], []
    for start in range(0, len(days) - train - test + 1, test):
        fit, trade = days[start:start + train], days[start + train:start + train + test]
        best, best_r, n_fit = None, None, 0
        for name, res in runs.items():
            ts = [t for t in res["trades"] if fit[0] <= t["date"] <= fit[-1]]
            if len(ts) < 10:
                continue  # too few trades to judge a variant on
            r = sum(t["r_multiple"] for t in ts) / len(ts)
            if best_r is None or r > best_r:
                best, best_r, n_fit = name, r, len(ts)
        if best is None:
            continue
        out = [t for t in runs[best]["trades"] if trade[0] <= t["date"] <= trade[-1]]
        unseen += out
        folds.append({"picked": best, "train_trades": n_fit, "train_avg_r": round(best_r, 3),
                      "test": bt.metrics(out), "test_days": "%s to %s" % (trade[0], trade[-1])})
    m = bt.metrics(unseen)
    return {"folds": folds, "unseen": m, "verdict": bt.verdict(_as_oos(m))}


def _as_oos(m: dict) -> dict:
    return m if m.get("trades") else {"trades": 0}


def walk_markdown(rep: dict, train: int = 30, test: int = 10) -> str:
    L = ["# Walk-forward", "",
         "Train on %d sessions, pick the best variant by avg R, trade it on the next %d, roll on. Net of costs." % (train, test),
         "", "**Verdict: %s**" % rep["verdict"], "",
         "| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |",
         "|---|---|---|---|---|---|---|"]
    for f in rep["folds"]:
        m = f["test"]
        if m.get("trades"):
            L.append("| %s | %s | %d | %+.3f | %d | %+.2f | %+.3f |" % (
                f["test_days"], f["picked"], f["train_trades"], f["train_avg_r"], m["trades"],
                m["expectancy_rs"], m["avg_r_net"]))
        else:
            L.append("| %s | %s | %d | %+.3f | 0 | | |" % (f["test_days"], f["picked"], f["train_trades"], f["train_avg_r"]))
    u = rep["unseen"]
    if u.get("trades"):
        L += ["", "All unseen trades: %d, net ₹%+.2f, avg %+.3fR." % (u["trades"], u["net_total"], u["avg_r_net"])]
    L.append("")
    return "\n".join(L)
