"""A fair contest between the main intraday strategy families, long and short.

The list and rules were fixed before the first run. Every strategy trades a fixed ₹25,000 at most once
per stock per day, pays the same charges and slippage, has a 1.5% stop, and exits at the 15:15 open.
To pass, a strategy must be net positive on the first two-thirds of sessions, then have a 95% lower
bound above zero on the last third, corrected for the number of strategies tried.

The stocks are today's Nifty 200, which flatters buying dips: stocks that collapsed left the list.
"""
from __future__ import annotations

import statistics

from .costs import CostModel
from .data import by_day
from .models import slip_pct

NOTIONAL = 25000.0
STOP_PCT = 1.5


def _first_close(bars, test, start=1):
    for i in range(start, len(bars) - 1):
        if test(bars[i]):
            return i
    return None


def _ret(bars, i):
    return (bars[i].close - bars[0].open) / bars[0].open * 100


# name: (side, rule(ctx) -> entry bar index or None)
STRATEGIES = {
    "opening range breakout": (1, lambda c: _first_close(c["bars"], lambda b: b.close > c["bars"][0].high)),
    "opening range breakdown": (-1, lambda c: _first_close(c["bars"], lambda b: b.close < c["bars"][0].low)),
    "gap and go, up": (1, lambda c: 0 if c["gap"] >= 1 else None),
    "gap and go, down": (-1, lambda c: 0 if c["gap"] <= -1 else None),
    "gap fade, down gap": (1, lambda c: 0 if c["gap"] <= -1 else None),
    "gap fade, up gap": (-1, lambda c: 0 if c["gap"] >= 1 else None),
    "first-hour momentum, up": (1, lambda c: 0 if _ret(c["bars"], 0) >= 1 else None),
    "first-hour momentum, down": (-1, lambda c: 0 if _ret(c["bars"], 0) <= -1 else None),
    "first-hour reversal, up move": (-1, lambda c: 0 if _ret(c["bars"], 0) >= 1 else None),
    "first-hour reversal, down move": (1, lambda c: 0 if _ret(c["bars"], 0) <= -1 else None),
    "prior-day high breakout": (1, lambda c: _first_close(c["bars"], lambda b: b.close > c["prev_high"], 0)),
    "prior-day low breakdown": (-1, lambda c: _first_close(c["bars"], lambda b: b.close < c["prev_low"], 0)),
    "afternoon momentum, up": (1, lambda c: 4 if len(c["bars"]) > 5 and _ret(c["bars"], 4) >= 1 else None),
    "afternoon momentum, down": (-1, lambda c: 4 if len(c["bars"]) > 5 and _ret(c["bars"], 4) <= -1 else None),
    "three down days, buy": (1, lambda c: 0 if c["streak"] <= -3 else None),
    "three up days, sell": (-1, lambda c: 0 if c["streak"] >= 3 else None),
    "narrow range breakout (NR7)": (1, lambda c: _first_close(c["bars"], lambda b: b.close > c["bars"][0].high) if c["nr7"] else None),
    "narrow range breakdown (NR7)": (-1, lambda c: _first_close(c["bars"], lambda b: b.close < c["bars"][0].low) if c["nr7"] else None),
    "relative strength vs Nifty": (1, lambda c: 1 if c["rs"] >= 1.5 else None),
    "relative weakness vs Nifty": (-1, lambda c: 1 if c["rs"] <= -1.5 else None),
}


def trade(bars: list, i: int, side: int, slip: float, costs: CostModel) -> tuple:
    """-> (gross ₹, net ₹) for one trade entered at bar i's close, on fixed notional."""
    last = len(bars) - 1
    entry = bars[i].close * (1 + side * slip)
    stop = entry * (1 - side * STOP_PCT / 100)
    exit_px = bars[last].open
    for b in bars[i + 1:last]:
        if side * (b.open - stop) <= 0:
            exit_px = b.open
            break
        if side * ((b.low if side > 0 else b.high) - stop) <= 0:
            exit_px = stop
            break
    exit_px *= 1 - side * slip
    qty = NOTIONAL / entry
    buy, sell = (entry, exit_px) if side > 0 else (exit_px, entry)
    gross = qty * side * (exit_px - entry)
    return gross, gross - costs.round_trip(qty * buy, qty * sell).total


def contexts(bars_all: list, index_days: dict, exclude_date=None):
    closes, ranges, prev = [], [], None
    for d, bars in sorted(by_day(bars_all).items()):
        if prev and d != exclude_date and len(bars) >= 6:
            streak = 0
            for a, b in zip(reversed(closes[:-1]), reversed(closes[1:])):
                step = 1 if b > a else -1
                if streak and (step > 0) != (streak > 0):
                    break
                streak += step
            idx = index_days.get(d, [])
            im = (idx[1].close - idx[0].open) / idx[0].open * 100 if len(idx) > 1 else 0.0
            yield d, {"bars": bars, "gap": (bars[0].open - prev["close"]) / prev["close"] * 100, "prev_high": prev["high"],
                      "prev_low": prev["low"], "streak": streak, "nr7": len(ranges) >= 7 and ranges[-1] <= min(ranges[-7:]),
                      "rs": _ret(bars, 1) - im}
        hi, lo = max(b.high for b in bars), min(b.low for b in bars)
        prev = {"close": bars[-1].close, "high": hi, "low": lo}
        closes.append(bars[-1].close)
        ranges.append(hi - lo)


def run(cfg: dict, history: dict, exclude_date=None) -> dict:
    index = cfg["regime"]["index"]
    costs = CostModel(cfg["costs"])
    slip = slip_pct(cfg) / 100
    index_days = by_day(history.get(index, []))
    days = sorted(d for d in index_days if d != exclude_date)
    cut = days[int(len(days) * 2 / 3)]
    results = {n: [] for n in STRATEGIES}
    for sym, bars in history.items():
        if sym == index:
            continue
        for d, ctx in contexts(bars, index_days, exclude_date):
            for name, (side, rule) in STRATEGIES.items():
                i = rule(ctx)
                if i is not None and i < len(ctx["bars"]) - 1:
                    results[name].append((d, side) + trade(ctx["bars"], i, side, slip, costs))
    z = statistics.NormalDist().inv_cdf(1 - 0.025 / len(STRATEGIES))
    rows = []
    for name, ts in results.items():
        early, late = [t for t in ts if t[0] < cut], [t for t in ts if t[0] >= cut]
        if len(early) < 30 or len(late) < 30:
            rows.append({"name": name, "side": STRATEGIES[name][0], "n": len(ts), "passed": False, "gross": 0.0, "early": 0.0, "late": 0.0, "low": 0.0})
            continue
        net_late = [t[3] for t in late]
        late_avg = statistics.mean(net_late)
        low = late_avg - z * statistics.stdev(net_late) / len(net_late) ** 0.5
        early_avg = statistics.mean(t[3] for t in early)
        rows.append({"name": name, "side": STRATEGIES[name][0], "n": len(ts), "gross": statistics.mean(t[2] for t in ts),
                     "early": early_avg, "late": late_avg, "low": low, "passed": early_avg > 0 and low > 0})
    rows.sort(key=lambda r: -r["late"])
    return {"first": str(days[0]), "last": str(days[-1]), "cut": str(cut), "sessions": len(days), "rows": rows}


def to_markdown(rep: dict) -> str:
    winners = [r["name"] for r in rep["rows"] if r["passed"]]
    L = ["# Strategy survey", "",
         "Hourly bars, about 200 stocks, %s to %s (%d sessions). ₹25,000 a trade, 1.5%% stop, out by 15:15. Confirmation period from %s." % (
             rep["first"], rep["last"], rep["sessions"], rep["cut"]),
         "", "**Passed: %s**" % (", ".join(winners) or "none"), "",
         "| strategy | side | trades | gross ₹/trade | early net ₹/trade | late net ₹/trade | late lower bound | pass |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        L.append("| %s | %s | %d | %+.2f | %+.2f | %+.2f | %+.2f | %s |" % (
            r["name"], "long" if r["side"] > 0 else "short", r["n"], r["gross"], r["early"], r["late"], r["low"], "yes" if r["passed"] else "no"))
    L += ["", "Stocks are today's Nifty 200, which flatters buying dips. Hourly bars hide what happens inside each hour.", ""]
    return "\n".join(L)
