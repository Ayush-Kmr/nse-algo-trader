"""The widest test available for free: first-hour breakouts on about 200 stocks over Yahoo's hourly
history (almost 3 years), scored on unseen sessions by the learned filter.

Hourly bars are coarser than the live 5-minute strategies, so this asks a general question: is there
any edge here in many market conditions? Yahoo reports zero volume on the 09:15 hourly bar, so
relative volume uses the next bar, which has closed before any signal fires.
"""
from __future__ import annotations

import statistics
from concurrent.futures import ThreadPoolExecutor

from . import backtest as bt
from . import data, learn, research
from .broker.paper import PaperBroker
from .costs import CostModel
from .data import by_day
from .models import Signal, round_tick, slip_pct

FEATURES = ["first_hour_range_pct", "gap_pct", "rel_volume", "move_from_open_pct", "index_move_pct",
            "rs_vs_index_pct", "bars_since_open", "index_green"]


def fetch(symbols: list) -> dict:
    def get(s):
        try:
            return s, data.fetch_bars(s, "730d", "60m", retries=2, timeout=25)
        except Exception:  # noqa: BLE001 - a missing stock narrows the test, it does not stop it
            return s, None
    with ThreadPoolExecutor(max_workers=6) as pool:
        return {s: b for s, b in pool.map(get, symbols) if b}


def rows(cfg: dict, history: dict, exclude_date=None) -> list:
    c = dict(cfg, bar_minutes=60)
    index = cfg["regime"]["index"]
    costs = CostModel(cfg["costs"])
    broker = PaperBroker(costs, slip_pct(cfg), cfg["tick_size"])
    tick = cfg["tick_size"]
    idx_days = by_day(history.get(index, []))
    out = []
    for sym, bars_all in history.items():
        if sym == index:
            continue
        vols, prev_close = [], None
        for d, bars in sorted(by_day(bars_all).items()):
            if d == exclude_date or len(bars) < 5:
                prev_close = bars[-1].close
                continue
            first, normal = bars[0], statistics.median(vols[-20:]) if len(vols) >= 20 else 0
            rel = bars[1].volume / normal if normal > 0 else None
            gap = (first.open - prev_close) / prev_close * 100 if prev_close else 0.0
            vols.append(bars[1].volume)
            prev_close = bars[-1].close
            width = (first.high - first.low) / first.low * 100 if first.low > 0 else 0
            if rel is None or not 0.3 <= width <= 4:
                continue
            for i in range(1, len(bars) - 1):
                b = bars[i]
                if b.close <= first.high:
                    continue
                entry, stop = round_tick(b.close, tick), round_tick(first.low, tick, "down")
                sig = Signal(sym, "hour_orb", entry, stop, round_tick(entry + 5 * (entry - stop), tick), b.ts, "")
                tr = research._walk(sig, bars, c, broker, costs)
                if tr:
                    seen = [x for x in idx_days.get(d, []) if x.ts <= b.ts]
                    im = (seen[-1].close - seen[0].open) / seen[0].open * 100 if seen else 0.0
                    mv = (b.close - first.open) / first.open * 100
                    out.append(dict(tr, date=d.isoformat(), gross_r=tr["gross_pnl"] / tr["planned_risk"], rel_volume=rel,
                                    x=[width, gap, min(rel, 10.0), mv, im, mv - im, float(i), 1.0 if im > 0 else 0.0]))
                break
    return out


def report(all_rows: list) -> dict:
    wf = learn.walk(all_rows, min_train=250, step=60)
    return {"sessions": len({r["date"] for r in all_rows}), "all": research.summarise(all_rows),
            "in_play_2x": research.summarise([r for r in all_rows if r["rel_volume"] >= 2]),
            "in_play_4x": research.summarise([r for r in all_rows if r["rel_volume"] >= 4]),
            "unseen": wf["unseen"], "picked": wf["picked"], "verdict": bt.verdict(wf["picked_metrics"])}


def to_markdown(rep: dict) -> str:
    L = ["# Long test", "", "First-hour breakouts, about 200 stocks, %d sessions, hourly bars, sized as a fresh account." % rep["sessions"],
         "", "**Learned filter on unseen sessions: %s**" % rep["verdict"], "",
         "| slice | signals | avg gross R | 95% interval | avg net R |", "|---|---|---|---|---|"]
    for name, key in (("all", "all"), ("volume 2x normal", "in_play_2x"), ("volume 4x normal", "in_play_4x"),
                      ("unseen sessions", "unseen"), ("picked by the model", "picked")):
        m = rep[key]
        if "avg_gross_r" in m:
            L.append("| %s | %d | %+.3f | %+.3f to %+.3f | %+.3f |" % (name, m["signals"], m["avg_gross_r"], m["gross_low"], m["gross_high"], m["avg_net_r"]))
        else:
            L.append("| %s | %d | | | |" % (name, m["signals"]))
    L.append("")
    return "\n".join(L)
