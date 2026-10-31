"""The rules of github.com/Jakeschincariol/day-trader-skill on NSE stocks, with Indian charges.

The rules are copied, not tuned: 15-minute range, first close above it, stop at the range midpoint,
1R or 2R target, and its five daily scanner setups. Its Time Machine is checked by asking whether its
odds, made only from earlier days, match what then happened. Daily results use today's Nifty 200, so
companies that failed are missing and the results are flattered.
"""
from __future__ import annotations

import random
import statistics

from .costs import CostModel
from .data import by_day
from .lab import NOTIONAL, metrics
from .models import slip_pct
from .timeutil import hhmm

MIN_RISK_PCT, LAST_BAR, REPLAYS, WINDOW, SEED = 0.05, 71, 200, 2, 19
SETUPS = ("breakout_20d", "bull_flag", "reclaim_ma20", "oversold", "oversold_bounce")
TESTS = 2 + len(SETUPS)


def walk(bars: list, entry: float, stop: float, target: float) -> tuple:
    """Stop beats target within a bar, gaps fill at the open, flat at 15:15. -> (exit price, outcome)"""
    flat = hhmm("15:15")
    for b in bars:
        if b.ts.time() >= flat:
            return b.open, "close"
        if b.open <= stop:
            return b.open, "stop"
        if b.low <= stop:
            return stop, "stop"
        if b.open >= target:
            return b.open, "target"
        if b.high >= target:
            return target, "target"
    return bars[-1].close, "close"


def net_of_costs(entry: float, out: float, slip: float, costs: CostModel) -> tuple:
    fill, sold = entry * (1 + slip), out * (1 - slip)
    qty = NOTIONAL / fill
    gross = qty * (sold - fill)
    return gross, gross - costs.round_trip(qty * fill, qty * sold).total


def orb_trades(history: dict, index: str, target_r: float, next_open: bool, slip: float, costs: CostModel) -> list:
    """next_open False is the repo's history replay, which fills at the signal bar's own close."""
    last = hhmm("14:45")
    out = []
    for sym, all_bars in history.items():
        if sym == index:
            continue
        for d, bars in sorted(by_day(all_bars).items()):
            if len(bars) < 30:
                continue
            hi, lo = max(b.high for b in bars[:3]), min(b.low for b in bars[:3])
            i = next((k for k in range(3, len(bars) - 1) if bars[k].close > hi), None)
            if i is None or bars[i].ts.time() > last:
                continue
            entry, stop = (bars[i + 1].open if next_open else bars[i].close), (hi + lo) / 2
            risk = entry - stop
            if risk < entry * MIN_RISK_PCT / 100:
                continue
            px, outcome = walk(bars[i + 1:], entry, stop, entry + target_r * risk)
            gross, net = net_of_costs(entry, px, slip, costs)
            out.append({"date": d, "symbol": sym, "r": (px - entry) / risk, "gross": gross, "net": net, "outcome": outcome,
                        "entry": entry, "stop": stop, "target": entry + target_r * risk, "start": i + 1})
    return out


def rsi_series(c: list, n: int = 14) -> list:
    """Wilder's RSI, one value per close."""
    out = [None] * len(c)
    if len(c) <= n:
        return out
    gains = [max(0.0, c[i] - c[i - 1]) for i in range(1, len(c))]
    falls = [max(0.0, c[i - 1] - c[i]) for i in range(1, len(c))]
    up, down = sum(gains[:n]) / n, sum(falls[:n]) / n
    for i in range(n, len(c)):
        if i > n:
            up, down = (up * (n - 1) + gains[i - 1]) / n, (down * (n - 1) + falls[i - 1]) / n
        out[i] = 100 - 100 / (1 + up / down) if down else 100.0
    return out


def setups_at(c: list, rsi: list, i: int) -> list:
    last, tags = c[i], []
    ma20, ma_prev = sum(c[i - 19:i + 1]) / 20, sum(c[i - 20:i]) / 20
    five = c[i - 4:i + 1]
    if last > max(c[i - 20:i]):
        tags.append("breakout_20d")
    if c[i - 5] / c[i - 15] - 1 > 0.10 and (max(five) - min(five)) / last < 0.05:
        tags.append("bull_flag")
    if c[i - 1] < ma_prev and last > ma20:
        tags.append("reclaim_ma20")
    if rsi[i] is not None and rsi[i] < 30:
        tags.append("oversold")
    if rsi[i - 1] is not None and rsi[i - 1] < 30 and last > c[i - 1]:
        tags.append("oversold_bounce")
    return tags


def daily_trades(daily: dict, slip: float, charges: float) -> tuple:
    """Buy the next day's open, sell its close. -> ({setup: trades}, {(symbol, trade date): setups})"""
    out, tags = {s: [] for s in SETUPS}, {}
    out["every stock, every day"] = []
    for sym, bars in daily.items():
        c = [b.close for b in bars]
        rsi = rsi_series(c)
        for i in range(30, len(bars) - 1):
            b = bars[i + 1]
            if b.open <= 0 or b.volume <= 0:
                continue
            fill, sold = b.open * (1 + slip), b.close * (1 - slip)
            gross = NOTIONAL * (sold / fill - 1)
            t = (b.ts.date(), gross, gross - charges)
            hits = setups_at(c, rsi, i)
            tags[(sym, b.ts.date())] = hits
            out["every stock, every day"].append(t)
            for s in hits:
                out[s].append(t)
    return out, tags


def lower_bound(trades: list, z: float) -> float:
    """Lower bound on ₹ a trade. Trades on one day move together, so the error comes from daily totals."""
    days = {}
    for t in trades:
        days[t[0]] = days.get(t[0], 0.0) + t[2]
    if len(days) < 2:
        return float("-inf")
    per_day = len(trades) / len(days)
    return (statistics.mean(days.values()) - z * statistics.stdev(days.values()) / len(days) ** 0.5) / per_day


def row(name: str, trades: list, z: float) -> dict:
    trades = sorted(trades, key=lambda t: t[0])
    mid = trades[len(trades) // 2][0] if trades else None
    m = metrics(trades)
    early, late = metrics([t for t in trades if t[0] < mid]), metrics([t for t in trades if t[0] >= mid])
    low = lower_bound(trades, z)
    return dict(m, name=name, low=low, early=early["expectancy"], late=late["expectancy"],
                gross=sum(t[1] for t in trades) / len(trades) if trades else 0.0,
                passed=len(trades) >= 100 and low > 0 and early["expectancy"] > 0 and late["expectancy"] > 0)


def replay(pool: dict, entry: float, stop: float, target: float, first: int, rng: random.Random) -> tuple:
    """The Time Machine's draws: each bar from the same time of day, within two bars. -> (target, stop)"""
    r, hit_t, hit_s = rng.random, 0, 0
    for _ in range(REPLAYS):
        p = entry
        for i in range(first, LAST_BAR + 1):
            options = pool[min(LAST_BAR, max(1, i + int(r() * (2 * WINDOW + 1)) - WINDOW))]
            hi, lo, cl = options[int(r() * len(options))]
            if p * lo <= stop:
                hit_s += 1
                break
            if p * hi >= target:
                hit_t += 1
                break
            p *= cl
    return hit_t, hit_s


def unbroken(bars: list) -> bool:
    """Yahoo often drops the last bars of a session, so only the bars before the 15:15 exit must be there."""
    return len(bars) > LAST_BAR and all((bars[i + 1].ts - bars[i].ts).total_seconds() == 300 for i in range(LAST_BAR))


def calibrate(history: dict, trades: list) -> list:
    """Time Machine odds from earlier days only, against what each 1R trade then did."""
    rng = random.Random(SEED)
    full = {s: sorted((d, b) for d, b in by_day(bars).items() if unbroken(b)) for s, bars in history.items()}
    out = []
    for t in trades:
        past = [b for d, b in full.get(t["symbol"], []) if d < t["date"]]
        if len(past) < 20 or t["start"] > LAST_BAR:
            continue
        pool = {j: [(b[j].high / b[j - 1].close, b[j].low / b[j - 1].close, b[j].close / b[j - 1].close) for b in past]
                for j in range(1, LAST_BAR + 1)}
        hit_t, hit_s = replay(pool, t["entry"], t["stop"], t["target"], t["start"], rng)
        if hit_t + hit_s:
            out.append((hit_t / (hit_t + hit_s), t))
    return out


def run(cfg: dict, history: dict, daily: dict) -> dict:
    index = cfg["regime"]["index"]
    costs, slip = CostModel(cfg["costs"]), slip_pct(cfg) / 100
    z = statistics.NormalDist().inv_cdf(1 - 0.025 / TESTS)
    triples = lambda ts: [(t["date"], t["gross"], t["net"]) for t in ts]  # noqa: E731
    trades = {(tr, nx): orb_trades(history, index, tr, nx, slip, costs) for tr in (1.0, 2.0) for nx in (True, False)}
    days, tags = daily_trades(daily, slip, costs.round_trip(NOTIONAL, NOTIONAL).total)
    orb = {}
    for (tr, nx), ts in trades.items():
        orb["%dR target, %s" % (tr, "next bar's open" if nx else "signal bar's close (repo's history)")] = dict(
            row("", triples(ts), z), r=statistics.mean(t["r"] for t in ts),
            outcomes={k: sum(t["outcome"] == k for t in ts) for k in ("target", "stop", "close")})
    pipeline = {s: row(s, triples([t for t in trades[(2.0, True)] if s in tags.get((t["symbol"], t["date"]), ())]), z) for s in SETUPS}
    checked = calibrate(history, trades[(1.0, True)])
    bands = []
    for name, lo, hi in (("under 45%", 0, .45), ("45% to 55%", .45, .55), ("55% and over", .55, 1.01)):
        mine = [(p, t) for p, t in checked if lo <= p < hi]
        sided = [t for _, t in mine if t["outcome"] != "close"]
        bands.append({"name": name, "n": len(mine), "predicted": 100 * statistics.mean(p for p, _ in mine) if mine else 0,
                      "actual": 100 * sum(t["outcome"] == "target" for t in sided) / len(sided) if sided else 0,
                      "net": statistics.mean(t["net"] for _, t in mine) if mine else 0})
    return {"orb": orb, "daily": [row(k, v, z) for k, v in days.items()], "pipeline": pipeline, "bands": bands,
            "symbols": len(history) - 1, "daily_symbols": len(daily),
            "first": min(t["date"] for t in trades[(2.0, True)]), "last": max(t["date"] for t in trades[(2.0, True)]),
            "daily_first": min(t[0] for t in days["every stock, every day"]), "daily_last": max(t[0] for t in days["every stock, every day"])}


def to_markdown(rep: dict) -> str:
    passed = [k for k, r in rep["orb"].items() if r["passed"]] + [r["name"] for r in rep["daily"] if r["passed"]]
    L = ["# Day-trader-skill rules on NSE", "", "Rules copied unchanged from the repo. ₹25,000 a trade, flat by 15:15, 0.06% a fill, Indian charges. "
         "A pass needs 100+ trades, a day-clustered lower bound above zero, and both halves positive.", "",
         "**%s**" % ("Passed: " + ", ".join(passed) if passed else "Nothing passed."), "",
         "## Opening-range breakout, midpoint stop", "",
         "%d stocks, %s to %s, Yahoo 5-minute bars." % (rep["symbols"], rep["first"], rep["last"]), "",
         "| version | trades | win % | avg R before costs | gross ₹/trade | net ₹/trade | net ₹ | PF | max DD ₹ | lower bound | pass |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in rep["orb"].items():
        L.append("| %s | %d | %.1f | %+.3f | %+.2f | %+.2f | %+.0f | %.2f | %.0f | %+.2f | %s |" % (
            k, r["trades"], r["win"], r["r"], r["gross"], r["expectancy"], r["net"], r["pf"] or 0, r["dd"], r["low"], "yes" if r["passed"] else "no"))
    L += ["", "## Daily scanner setups, next day open to close", "", "%d of today's stocks, %s to %s, Yahoo daily bars. Survivorship flatters these." % (
        rep["daily_symbols"], rep["daily_first"], rep["daily_last"]), "",
        "| setup | trades | win % | gross ₹/trade | net ₹/trade | early half | late half | lower bound | pass |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rep["daily"]:
        L.append("| %s | %d | %.1f | %+.2f | %+.2f | %+.2f | %+.2f | %+.2f | %s |" % (
            r["name"], r["trades"], r["win"], r["gross"], r["expectancy"], r["early"], r["late"], r["low"], "yes" if r["passed"] else "no"))
    L += ["", "## The full pipeline: yesterday's setup, then today's breakout (2R, next open)", "",
          "| setup | trades | win % | gross ₹/trade | net ₹/trade | net ₹ |", "|---|---|---|---|---|---|"]
    for r in rep["pipeline"].values():
        L.append("| %s | %d | %.1f | %+.2f | %+.2f | %+.0f |" % (r["name"], r["trades"], r["win"], r["gross"], r["expectancy"], r["net"]))
    L += ["", "## Time Machine odds against what happened (1R trades)", "",
          "Odds use %d replays from earlier days of the same stock, seed %d." % (REPLAYS, SEED), "",
          "| its odds of target first | trades | average odds % | actual target first % | net ₹/trade |", "|---|---|---|---|---|"]
    for b in rep["bands"]:
        L.append("| %s | %d | %.1f | %.1f | %+.2f |" % (b["name"], b["n"], b["predicted"], b["actual"], b["net"]))
    L.append("")
    return "\n".join(L)
