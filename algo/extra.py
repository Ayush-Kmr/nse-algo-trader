"""The remaining intraday tests. Rules were fixed before the first run.

- Finer timing: opening-range breaks from the first 5 and 15 minutes, on 5-minute bars (about 60 days).
- News proxy: 3%+ gaps on 3x normal volume. There is no free news history, so this is a stand-in.
- Pairs: same-industry stocks, most correlated over the past 120 days, 2-sigma spread, closed the same day.

Options and order-book strategies are not here because no honest free history exists.
"""
from __future__ import annotations

import csv
import math
import statistics

from .costs import CostModel
from .data import by_day
from .models import slip_pct
from .survey import NOTIONAL, _first_close, contexts, trade

MIN_TRADES = 30


def _corr(a: list, b: list) -> float:
    ma, mb = statistics.mean(a), statistics.mean(b)
    top = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return top / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5


def summary(name: str, side: str, ts: list, cut, tests: int) -> dict:
    early, late = [t for t in ts if t[0] < cut], [t for t in ts if t[0] >= cut]
    row = {"name": name, "side": side, "n": len(ts), "gross": 0.0, "early": 0.0, "late": 0.0, "low": 0.0, "passed": False}
    if len(early) < MIN_TRADES or len(late) < MIN_TRADES:
        return row
    z = statistics.NormalDist().inv_cdf(1 - 0.025 / tests)
    net = [t[2] for t in late]
    row.update(gross=statistics.mean(t[1] for t in ts), early=statistics.mean(t[2] for t in early), late=statistics.mean(net),
               low=statistics.mean(net) - z * statistics.stdev(net) / len(net) ** 0.5)
    row["passed"] = row["early"] > 0 and row["low"] > 0
    return row


def finer(cfg: dict, history: dict, exclude_date=None) -> list:
    costs, slip = CostModel(cfg["costs"]), slip_pct(cfg) / 100
    days = sorted({d for b in history.values() for d in by_day(b) if d != exclude_date})
    cut = days[int(len(days) * 2 / 3)]
    tests = {"5-minute range breakout": (1, 1), "5-minute range breakdown": (-1, 1),
             "15-minute range breakout": (1, 3), "15-minute range breakdown": (-1, 3)}
    out = {n: [] for n in tests}
    for sym, bars_all in history.items():
        if sym.startswith("^"):
            continue
        for d, bars in by_day(bars_all).items():
            if d == exclude_date or len(bars) < 40:
                continue
            for name, (side, n) in tests.items():
                hi, lo = max(b.high for b in bars[:n]), min(b.low for b in bars[:n])
                i = _first_close(bars, (lambda b: b.close > hi) if side > 0 else (lambda b: b.close < lo), n)
                if i is not None:
                    out[name].append((d,) + trade(bars, i, side, slip, costs))
    return [summary(n, "long" if tests[n][0] > 0 else "short", t, cut, len(tests)) for n, t in out.items()]


def _rsi(closes: list, n: int = 14) -> list:
    out, up, down = [50.0] * len(closes), 0.0, 0.0
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gain, loss = max(ch, 0.0), max(-ch, 0.0)
        up, down = (up * (n - 1) + gain) / n, (down * (n - 1) + loss) / n
        out[i] = 100 - 100 / (1 + up / down) if down else 100.0
    return out


def _ema(xs: list, n: int) -> list:
    out, k = [xs[0]], 2 / (n + 1)
    for x in xs[1:]:
        out.append(out[-1] + k * (x - out[-1]))
    return out


def divergence(bars: list, side: int, use_macd: bool = False):
    """First bar with a new 25-bar extreme that the oscillator does not confirm, closing back the other way."""
    closes = [b.close for b in bars]
    osc = [a - b for a, b in zip(_ema(closes, 12), _ema(closes, 26))] if use_macd else _rsi(closes)
    for i in range(30, len(bars) - 1):
        if bars[i].ts.hour >= 14 and bars[i].ts.minute >= 45 or bars[i].ts.hour > 14:
            return None
        b = bars[i]
        past = range(i - 30, i - 5)
        if side > 0:
            j = min(past, key=lambda k: bars[k].low)
            if b.low < bars[j].low and osc[i] > osc[j] and b.close > b.open and (use_macd or osc[i] < 35):
                return i
        else:
            j = max(past, key=lambda k: bars[k].high)
            if b.high > bars[j].high and osc[i] < osc[j] and b.close < b.open and (use_macd or osc[i] > 65):
                return i
    return None


def guide(cfg: dict, history: dict, exclude_date=None) -> list:
    """Groww's guide gives no full rules, so these were fixed here: RSI 14 and MACD 12/26 divergence on
    5-minute bars, and its 3%+ gap with a 15-minute range break. Same costs, 1.5% stop, out by the close."""
    costs, slip = CostModel(cfg["costs"]), slip_pct(cfg) / 100
    days = sorted({d for b in history.values() for d in by_day(b) if d != exclude_date})
    cut = days[int(len(days) * 2 / 3)]
    tests = {"RSI divergence, buy": 1, "RSI divergence, sell": -1, "MACD divergence, buy": 1, "MACD divergence, sell": -1,
             "3% gap up, range break": 1, "3% gap down, range break": -1}
    out = {n: [] for n in tests}
    for sym, bars_all in history.items():
        if sym.startswith("^"):
            continue
        prev = None
        for d, bars in sorted(by_day(bars_all).items()):
            if d != exclude_date and len(bars) >= 40:
                for name, side in tests.items():
                    if name.startswith("3%"):
                        gap = (bars[0].open - prev) / prev * 100 if prev else 0.0
                        if side * gap < 3:
                            continue
                        hi, lo = max(b.high for b in bars[:3]), min(b.low for b in bars[:3])
                        i = _first_close(bars, (lambda b: b.close > hi) if side > 0 else (lambda b: b.close < lo), 3)
                    else:
                        i = divergence(bars, side, name.startswith("MACD"))
                    if i is not None:
                        out[name].append((d,) + trade(bars, i, side, slip, costs))
            prev = bars[-1].close
    return [summary(n, "long" if tests[n] > 0 else "short", t, cut, len(tests)) for n, t in out.items()]


def news_proxy(cfg: dict, history: dict, exclude_date=None) -> list:
    costs, slip = CostModel(cfg["costs"]), slip_pct(cfg) / 100
    index = cfg["regime"]["index"]
    days = sorted(d for d in by_day(history[index]) if d != exclude_date)
    cut = days[int(len(days) * 2 / 3)]
    tests = {"follow the gap": 1, "fade the gap": -1}
    out = {n: [] for n in tests}
    for sym, bars_all in history.items():
        if sym == index:
            continue
        vols = {}
        ordered = sorted(by_day(bars_all).items())
        for k, (d, bars) in enumerate(ordered):
            vols[d] = bars[1].volume if len(bars) > 1 else 0.0
        hist = [vols[d] for d, _ in ordered]
        pos = {d: k for k, (d, _) in enumerate(ordered)}
        for d, ctx in contexts(bars_all, {}, exclude_date):
            k = pos[d]
            normal = statistics.median(hist[max(0, k - 20):k]) if k >= 20 else 0
            if normal <= 0 or hist[k] / normal < 3 or abs(ctx["gap"]) < 3:
                continue
            for name, sign in tests.items():
                out[name].append((d,) + trade(ctx["bars"], 1, sign * (1 if ctx["gap"] > 0 else -1), slip, costs))
    return [summary(n, "both", t, cut, len(tests)) for n, t in out.items()]


def pairs(cfg: dict, history: dict, industry: dict, exclude_date=None, top: int = 30) -> list:
    costs, slip = CostModel(cfg["costs"]), slip_pct(cfg) / 100
    index = cfg["regime"]["index"]
    days = sorted(d for d in by_day(history[index]) if d != exclude_date)
    cut = days[int(len(days) * 2 / 3)]
    bars = {s: by_day(b) for s, b in history.items() if s != index}
    close = {s: {d: v[-1].close for d, v in m.items()} for s, m in bars.items()}
    groups = {}
    for s in bars:
        groups.setdefault(industry.get(s, "?"), []).append(s)
    trades, chosen = [], []

    def leg(px_in, px_out, side):
        entry, out = px_in * (1 + side * slip), px_out * (1 - side * slip)
        qty = NOTIONAL / 2 / entry
        buy, sell = (entry, out) if side > 0 else (out, entry)
        gross = qty * side * (out - entry)
        return gross, gross - costs.round_trip(qty * buy, qty * sell).total

    for k in range(120, len(days)):
        if (k - 120) % 60 == 0:  # reselect on past data only
            window = days[k - 120:k]
            scored = []
            for members in groups.values():
                rets = {}
                for s in members:
                    c = [close[s].get(d) for d in window]
                    if all(c):
                        rets[s] = [b / a - 1 for a, b in zip(c, c[1:])]
                names = sorted(rets)
                for i, a in enumerate(names):
                    for b in names[i + 1:]:
                        if statistics.pstdev(rets[a]) and statistics.pstdev(rets[b]):
                            scored.append((_corr(rets[a], rets[b]), a, b))
            chosen = sorted(scored, reverse=True)[:top]
        d = days[k]
        for _, a, b in chosen:
            ba, bb = bars[a].get(d), bars[b].get(d)
            past = [(close[a].get(x), close[b].get(x)) for x in days[k - 60:k]]
            if not ba or not bb or len(ba) < 4 or len(bb) < 4 or not all(x and y for x, y in past):
                continue
            spread = [math.log(x / y) for x, y in past]
            sd = statistics.pstdev(spread)
            if not sd:
                continue
            z = (math.log(ba[1].close / bb[1].close) - statistics.mean(spread)) / sd
            if abs(z) < 2:
                continue
            side = -1 if z > 0 else 1  # short the rich leg, buy the cheap one
            g1, n1 = leg(ba[1].close, ba[-1].open, side)
            g2, n2 = leg(bb[1].close, bb[-1].open, -side)
            trades.append((d, g1 + g2, n1 + n2))
    return [summary("same-industry pairs", "both", trades, cut, 1)]


def load_industries(path: str) -> dict:
    with open(path, newline="") as fh:
        return {r["Symbol"].strip(): r["Industry"].strip() for r in csv.DictReader(fh)}


def to_markdown(sections: dict) -> str:
    L = ["# Other intraday tests", "", "₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.", ""]
    for title, rows in sections.items():
        L += ["## " + title, "", "| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |", "|---|---|---|---|---|---|---|---|"]
        L += ["| %s | %s | %d | %+.2f | %+.2f | %+.2f | %+.2f | %s |" % (
            r["name"], r["side"], r["n"], r["gross"], r["early"], r["late"], r["low"], "yes" if r["passed"] else "no") for r in rows]
        L.append("")
    return "\n".join(L)
