"""Research lab: four strategy families, long and short, with strict chronological splits.

Sessions are split 60/20/20. Settings are chosen on training only. A family continues only if its
chosen settings are net positive on validation. Test sessions score only the finalists, once. Entries
fill at the next bar's open, so a signal never trades on the bar that created it.
"""
from __future__ import annotations

import statistics

from . import features
from .costs import CostModel
from .data import by_day
from .models import slip_pct
from .timeutil import hhmm

NOTIONAL = 25000.0
STOPS, TARGETS = (1.0, 1.5, 2.0), (1.5, 2.0, 3.0)


def orb(bars, f, i, side):
    if len(bars[:i]) < 3:
        return False
    hi, lo = max(b.high for b in bars[:3]), min(b.low for b in bars[:3])
    first = all(not (side * (b.close - (hi if side > 0 else lo)) > 0) for b in bars[3:i])
    rv = f["rvol"][i]
    return i >= 3 and first and side * (bars[i].close - (hi if side > 0 else lo)) > 0 and (rv is None or rv >= 1.5)


def vwap_continuation(bars, f, i, side):
    if i < 9 or f["vwap"][i] is None:
        return False
    b = bars[i]
    aligned = side * (f["ema9"][i] - f["ema20"][i]) > 0 and side * (f["ema20"][i] - f["ema50"][i]) > 0
    touched = (b.low <= f["ema20"][i]) if side > 0 else (b.high >= f["ema20"][i])
    return aligned and touched and side * (b.close - f["vwap"][i]) > 0 and side * (b.close - b.open) > 0


def trend(bars, f, i, side):
    if i < 9 or f["vwap"][i] is None:
        return False
    was = side * (f["ema9"][i - 1] - f["ema20"][i - 1]) <= 0
    return was and side * (f["ema9"][i] - f["ema20"][i]) > 0 and side * (bars[i].close - f["vwap"][i]) > 0


def mean_reversion(bars, f, i, side):
    if i < 9 or f["vwap"][i] is None:
        return False
    stretched = side * (f["vwap"][i] - bars[i].close) > 2 * f["atr"][i]
    rsi_ok = f["rsi"][i] < 25 if side > 0 else f["rsi"][i] > 75
    return stretched and rsi_ok and side * (bars[i].close - bars[i].open) > 0


FAMILIES = {"opening-range breakout": orb, "VWAP continuation": vwap_continuation, "trend following": trend, "mean reversion": mean_reversion}


def signals(history: dict, index: str, cfg: dict, exclude_date=None) -> list:
    """One entry per stock, day, family and side: (family, side, date, bars, entry index, ATR)."""
    idx = by_day(history.get(index, []))
    last = hhmm("14:45")
    out = []
    for sym, bars_all in history.items():
        if sym == index:
            continue
        past = []
        for d, bars in sorted(by_day(bars_all).items()):
            if d != exclude_date and len(bars) >= 30:
                f = features.compute(bars, past, idx.get(d, []))
                for name, rule in FAMILIES.items():
                    for side in (1, -1):
                        for i in range(3, len(bars) - 1):
                            if bars[i].ts.time() > last:
                                break
                            if f["market"] and f["market"].get(bars[i].ts) == -side and name != "mean reversion":
                                continue
                            if rule(bars, f, i, side):
                                out.append((name, side, d, sym, bars, i, f["atr"][i]))
                                break
            past.append(bars)
    return out


def exit_trade(bars, i, side, atr, stop_atr, target_atr, slip, costs):
    """Fills at the next open. Stop beats target in one bar; gaps fill at the open. -> (gross, net, date)"""
    fill = bars[i + 1].open * (1 + side * slip)
    stop, target = fill - side * stop_atr * atr, fill + side * target_atr * atr
    close_at = hhmm("15:15")
    px = None
    for b in bars[i + 1:]:
        if b.ts.time() >= close_at:
            px = b.open
            break
        if side * (b.open - stop) <= 0:
            px = b.open
            break
        if side * ((b.low if side > 0 else b.high) - stop) <= 0:
            px = stop
            break
        if side * ((b.high if side > 0 else b.low) - target) >= 0:
            px = target
            break
    px = bars[-1].close if px is None else px
    out = px * (1 - side * slip)
    qty = NOTIONAL / fill
    buy, sell = (fill, out) if side > 0 else (out, fill)
    gross = qty * side * (out - fill)
    return gross, gross - costs.round_trip(qty * buy, qty * sell).total


def metrics(trades: list) -> dict:
    """trades: [(date, gross, net)]"""
    if not trades:
        return {"trades": 0, "net": 0.0, "win": 0.0, "pf": None, "expectancy": 0.0, "dd": 0.0, "monthly": {}, "se": 0.0}
    net = [t[2] for t in trades]
    gains, losses = sum(x for x in net if x > 0), -sum(x for x in net if x <= 0)
    eq, peak, dd, monthly = 0.0, 0.0, 0.0, {}
    for t in sorted(trades, key=lambda t: t[0]):
        eq += t[2]
        peak, dd = max(peak, eq), max(dd, peak - eq)
        key = t[0].strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0.0) + t[2]
    return {"trades": len(net), "net": sum(net), "win": 100 * sum(x > 0 for x in net) / len(net), "pf": gains / losses if losses else None,
            "expectancy": sum(net) / len(net), "dd": dd, "monthly": monthly,
            "se": statistics.stdev(net) / len(net) ** 0.5 if len(net) > 1 else 0.0}


def run(cfg: dict, history: dict, exclude_date=None) -> dict:
    index = cfg["regime"]["index"]
    costs, slip = CostModel(cfg["costs"]), slip_pct(cfg) / 100
    sig = signals(history, index, cfg, exclude_date)
    days = sorted({s[2] for s in sig})
    a, b = days[int(len(days) * .6)], days[int(len(days) * .8)]
    z = statistics.NormalDist().inv_cdf(1 - 0.025 / (len(FAMILIES) * 2))
    rows = []
    for name in FAMILIES:
        for side in (1, -1):
            mine = [s for s in sig if s[0] == name and s[1] == side]

            def trades(when, st, tg):
                return [(s[2],) + exit_trade(s[4], s[5], side, s[6], st, tg, slip, costs) for s in mine if when(s[2])]
            best = max(((metrics(trades(lambda d: d < a, st, tg))["expectancy"], st, tg) for st in STOPS for tg in TARGETS))
            _, st, tg = best
            tr, va = metrics(trades(lambda d: d < a, st, tg)), metrics(trades(lambda d: a <= d < b, st, tg))
            row = {"name": name, "side": "long" if side > 0 else "short", "stop": st, "target": tg, "train": tr, "validation": va}
            if va["trades"] >= 30 and va["expectancy"] > 0:
                te = metrics(trades(lambda d: d >= b, st, tg))
                row["test"] = te
                row["passed"] = te["trades"] >= 30 and te["expectancy"] - z * te["se"] > 0
            else:
                row["passed"] = False
            rows.append(row)
    return {"first": str(days[0]), "last": str(days[-1]), "valid_from": str(a), "test_from": str(b), "sessions": len(days), "rows": rows}


def to_markdown(rep: dict, source: str) -> str:
    winners = [r for r in rep["rows"] if r["passed"]]
    L = ["# Strategy lab", "", "Source: %s. %s to %s (%d sessions). Validation from %s, test from %s. ₹25,000 a trade, next-bar fills, all charges." % (
        source, rep["first"], rep["last"], rep["sessions"], rep["valid_from"], rep["test_from"]), "",
        "**%s**" % ("Positive out-of-sample edge: " + ", ".join("%s (%s)" % (r["name"], r["side"]) for r in winners)
                    if winners else "No reliable trading edge was found."), "",
        "| strategy | side | stop, target (ATR) | train trades | train ₹/trade | val trades | val ₹/trade | val win % | val PF | val net ₹ | val max DD ₹ | test | pass |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        t, v = r["train"], r["validation"]
        test = "%d trades, ₹%+.2f" % (r["test"]["trades"], r["test"]["expectancy"]) if "test" in r else "not reached"
        L.append("| %s | %s | %.1f, %.1f | %d | %+.2f | %d | %+.2f | %.1f | %s | %+.0f | %.0f | %s | %s |" % (
            r["name"], r["side"], r["stop"], r["target"], t["trades"], t["expectancy"], v["trades"], v["expectancy"], v["win"],
            "%.2f" % v["pf"] if v["pf"] else "-", v["net"], v["dd"], test, "yes" if r["passed"] else "no"))
    L += ["", "## Monthly net ₹, validation", "", "| strategy | side | months |", "|---|---|---|"]
    for r in rep["rows"]:
        L.append("| %s | %s | %s |" % (r["name"], r["side"], ", ".join("%s %+.0f" % kv for kv in sorted(r["validation"]["monthly"].items())) or "none"))
    L.append("")
    return "\n".join(L)
