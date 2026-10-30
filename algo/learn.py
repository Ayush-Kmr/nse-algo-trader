"""Can a model pick the good signals? Ridge regression on what is known when a signal fires.

Walk-forward by day: fit on earlier sessions only, score the next block, roll on. Features are
standardised on the training days alone. Standard library only, and research only: nothing here
reaches the engine.
"""
from __future__ import annotations

import statistics

from . import backtest as bt
from . import research
from .experiments import deep_merge
from .strategies import REGISTRY
from .strategies.vwap_reclaim import session_vwap

FEATURES = ["day_range_pct", "move_from_open_pct", "vs_vwap_pct", "stop_pct", "rel_volume", "rs_vs_index_pct",
            "minutes_since_open"] + ["is_" + s for s in sorted(REGISTRY)]


def features(sig, bars: list, index_bars: list) -> list:
    """Only bars up to and including the signal bar."""
    seen = [b for b in bars if b.ts <= sig.bar_ts]
    idx = [b for b in index_bars if b.ts <= sig.bar_ts]
    o, last = seen[0].open, seen[-1]
    vw = session_vwap(seen)[-1] or last.close
    prior = [b.volume for b in seen[1:-1]]
    move = (last.close - o) / o * 100
    idx_move = (idx[-1].close - idx[0].open) / idx[0].open * 100 if idx else 0.0
    return [(max(b.high for b in seen) - min(b.low for b in seen)) / o * 100, move,
            (last.close - vw) / vw * 100, (sig.entry - sig.stop) / sig.entry * 100,
            last.volume / statistics.median(prior) if prior and statistics.median(prior) > 0 else 1.0,
            move - idx_move, len(seen) * 5.0] + [1.0 if sig.strategy == s else 0.0 for s in sorted(REGISTRY)]


def ridge(X: list, y: list, lam: float = 10.0) -> list:
    """Solve (X'X + lam I) w = X'y by Gaussian elimination. X already has its intercept column."""
    n = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) + (lam if i == j and i else 0.0) for j in range(n)]
         + [sum(r[i] * t for r, t in zip(X, y))] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(A[k][i]))
        A[i], A[p] = A[p], A[i]
        if abs(A[i][i]) < 1e-12:
            continue
        for k in range(n):
            if k != i:
                f = A[k][i] / A[i][i]
                A[k] = [a - f * b for a, b in zip(A[k], A[i])]
    return [A[i][n] / A[i][i] if abs(A[i][i]) >= 1e-12 else 0.0 for i in range(n)]


def _scaler(X: list):
    cols = list(zip(*X))
    mean = [sum(c) / len(c) for c in cols]
    sd = [statistics.pstdev(c) or 1.0 for c in cols]
    return lambda r: [1.0] + [(v - m) / s for v, m, s in zip(r, mean, sd)]


def predict(w: list, x: list) -> float:
    return sum(a * b for a, b in zip(w, x))


def walk(rows: list, min_train: int = 30, step: int = 10, threshold: float = 0.28) -> dict:
    days = sorted({r["date"] for r in rows})
    all_unseen, picked = [], []
    for start in range(min_train, len(days), step):
        train_days, test_days = set(days[:start]), set(days[start:start + step])
        tr = [r for r in rows if r["date"] in train_days]
        scale = _scaler([r["x"] for r in tr])
        w = ridge([scale(r["x"]) for r in tr], [r["gross_r"] for r in tr])
        for r in rows:
            if r["date"] in test_days:
                all_unseen.append(r)
                if predict(w, scale(r["x"])) > threshold:
                    picked.append(r)
    return {"unseen": research.summarise(all_unseen), "picked": research.summarise(picked),
            "picked_metrics": bt.metrics(picked), "verdict": bt.verdict(bt.metrics(picked))}


def run(cfg: dict, history: dict, exclude_date=None) -> dict:
    c = deep_merge(cfg, {"strategies": sorted(REGISTRY), "regime": {"require_green_day": False}})
    rows = research.signal_rows(c, history, exclude_date, feature_fn=features)
    return dict(walk(rows), signals=len(rows), sessions=len({r["date"] for r in rows}))


def to_markdown(rep: dict) -> str:
    def row(name, m):
        if "avg_gross_r" not in m:
            return "| %s | %d | | | |" % (name, m["signals"])
        return "| %s | %d | %+.3f | %+.3f to %+.3f | %+.3f |" % (
            name, m["signals"], m["avg_gross_r"], m["gross_low"], m["gross_high"], m["avg_net_r"])
    return "\n".join(["# Learned signal filter", "",
                      "%d signals over %d sessions, all strategies, no regime filter. Ridge regression on features known"
                      " at the signal, fitted on earlier sessions only and scored on unseen ones." % (rep["signals"], rep["sessions"]),
                      "", "**Verdict: %s**" % rep["verdict"], "",
                      "| unseen signals | count | avg gross R | 95% interval | avg net R |", "|---|---|---|---|---|",
                      row("all", rep["unseen"]), row("picked by the model", rep["picked"]), "",
                      "Signals on the same day move together, so these intervals are narrower than they should be.", ""])
