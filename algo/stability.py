"""Stress test: the full history through the live tick path, with faults injected.

Every tick starts a fresh Engine from JSON, as a GitHub Actions run does. Clean replays must match the
backtest exactly. Chaos replays drop ticks, symbols and the index, and every safety rule must still
hold. Charts are drawn for every alert. Nothing is sent or saved.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from . import backtest as bt
from .chart import alert_image
from .data import by_day
from .engine import Engine, new_state
from .timeutil import hhmm


def replay(cfg: dict, history: dict, exclude_date=None, seed=None, drop_tick=0.0, drop_symbol=0.0, drop_index=0.0) -> dict:
    rng = random.Random(seed)
    index = cfg["regime"]["index"]
    days_by_sym = {s: by_day(b) for s, b in history.items()}
    days = sorted({d for m in days_by_sym.values() for d in m if d != exclude_date})
    open_t, sq = hhmm(cfg["session_open"]), hhmm(cfg["square_off"])
    state = new_state(cfg)
    out = {"trades": [], "ticks": 0, "skipped": 0, "charts": 0, "chart_errors": 0, "carried": 0, "breaches": [],
           "worst_day_pct": 0.0, "max_open": 0, "max_entries": 0}
    for d in days:
        day = {s: [b for b in m.get(d, []) if b.ts.time() >= open_t] for s, m in days_by_sym.items()}
        stamps = sorted({b.ts for bars in day.values() for b in bars})
        if not stamps:
            continue
        start_equity = state["equity"]
        for ts in stamps:
            now = ts + timedelta(minutes=cfg["bar_minutes"])
            if rng.random() < drop_tick and now.time() < sq:
                out["skipped"] += 1
                continue
            view = {}
            for s, bars in day.items():
                if s != index and rng.random() < drop_symbol:
                    continue
                view[s] = [b for b in bars if b.ts <= ts]
            index_bars = view.pop(index, None)
            if rng.random() < drop_index:
                index_bars = None

            def notify(ev):
                if ev["kind"] in ("ENTRY", "EXIT") and view.get(ev["symbol"]):
                    try:
                        alert_image(ev, view[ev["symbol"]])
                        out["charts"] += 1
                    except Exception:  # noqa: BLE001 - counted and reported
                        out["chart_errors"] += 1

            state = json.loads(json.dumps(state))  # a tick only has what was saved
            Engine(cfg, state, notify=notify).step(now, view, index_bars, live=seed is not None)
            out["ticks"] += 1
            out["max_open"] = max(out["max_open"], len(state["positions"]))
            if now.time() > sq and not state["positions"]:
                break
        if state["positions"] and stamps:
            last = stamps[-1] + timedelta(minutes=cfg["bar_minutes"])
            flat_at = datetime.combine(d, sq, last.tzinfo) if last.time() < sq else last
            Engine(cfg, state).step(flat_at, {s: b for s, b in day.items() if s != index}, day.get(index))
        t = state["today"]
        out["trades"] += [dict(x, date=d.isoformat()) for x in t["trades"]]
        out["max_entries"] = max(out["max_entries"], t["entries"])
        out["carried"] += 1 if state["positions"] else 0
        out["worst_day_pct"] = min(out["worst_day_pct"], t["realised"] / start_equity * 100)
        symbols = [x["symbol"] for x in t["trades"]]
        if len(symbols) != len(set(symbols)):
            out["breaches"].append("%s: symbol traded twice" % d)
    out["final_equity"] = state["equity"]
    limit_open, limit_entries = cfg["max_open_positions"], cfg["max_trades_per_day"]
    if out["max_open"] > limit_open:
        out["breaches"].append("open positions reached %d" % out["max_open"])
    if out["max_entries"] > limit_entries:
        out["breaches"].append("entries reached %d" % out["max_entries"])
    if out["worst_day_pct"] < -cfg["daily_loss_limit_pct"] * 1.1:
        out["breaches"].append("worst day %.2f%%" % out["worst_day_pct"])
    return out


CHAOS = [("mild", dict(drop_tick=0.05, drop_symbol=0.02, drop_index=0.02)),
         ("bad", dict(drop_tick=0.2, drop_symbol=0.1, drop_index=0.1)),
         ("severe", dict(drop_tick=0.5, drop_symbol=0.3, drop_index=0.3))]


def run(cfg: dict, history: dict, exclude_date=None, seeds=(1, 2, 3, 4, 5)) -> dict:
    key = lambda t: (t["date"], t["symbol"], t["entry_ts"], t["exit_ts"], t["net_pnl"])  # noqa: E731
    base = bt.run(cfg, history, cfg["regime"]["index"], exclude_date)
    clean = replay(cfg, history, exclude_date)
    rows = [{"name": "clean, saved and reloaded every tick", "seed": "-", **clean}]
    for name, faults in CHAOS:
        for seed in seeds:
            rows.append({"name": name, "seed": seed, **replay(cfg, history, exclude_date, seed=seed, **faults)})
    return {"identical": sorted(map(key, base["trades"])) == sorted(map(key, clean["trades"])),
            "base_trades": len(base["trades"]), "clean_trades": len(clean["trades"]), "rows": rows}


def passed(rep: dict) -> bool:
    return rep["identical"] and not any(r["breaches"] or r["chart_errors"] for r in rep["rows"])


def to_markdown(rep: dict) -> str:
    L = ["# Stability test", "", "**Result: %s**" % ("PASS" if passed(rep) else "FAIL"), "",
         "Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **%s** (%d and %d trades)." % (
             rep["identical"], rep["base_trades"], rep["clean_trades"]), "",
         "| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        L.append("| %s | %s | %d | %d | %d | %d | %d | %.2f | %d | %d | %d | %s |" % (
            r["name"], r["seed"], r["ticks"], r["skipped"], len(r["trades"]), r["charts"], r["chart_errors"],
            r["worst_day_pct"], r["max_open"], r["max_entries"], r["carried"], "; ".join(r["breaches"]) or "none"))
    L += ["", "This tests that the software holds up. It says nothing about whether the strategy makes money.", ""]
    return "\n".join(L)
