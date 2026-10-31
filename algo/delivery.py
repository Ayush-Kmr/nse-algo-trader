"""Multi-month delivery strategies on daily closes, with real delivery charges on ₹50,000.

Rules were fixed before the first run. Portfolios of 10 equal slots rebalance monthly, and prices
exclude dividends for every strategy and benchmark.

The stocks are today's Nifty 200, so companies that failed are missing and every long-history result
is flattered. To allow for that, a strategy must beat a plain equal-weight hold of the same stocks,
which carries the same bias, as well as the Nifty ETF, in both halves of the period.
"""
from __future__ import annotations

import statistics
from concurrent.futures import ThreadPoolExecutor

from . import bhav, data

CAPITAL, SLOTS, TOP = 50000.0, 10, 200
ETF, INDEX = "NIFTYBEES", "^NSEI"
STT, EXCH, SEBI, STAMP, GST, DP, SLIP = 0.001, 0.000030699, 0.000001, 0.00015, 0.18, 20.0, 0.0006
TESTS = 8


def fetch(symbols: list) -> tuple:
    """-> ({symbol: {date: close}}, {symbol: {date: rupees traded}})"""
    def get(s):
        try:
            return s, data.fetch_bars(s, "20y", "1d", retries=2, timeout=30)
        except Exception:  # noqa: BLE001 - a missing stock narrows the test, it does not stop it
            return s, None
    with ThreadPoolExecutor(max_workers=6) as pool:
        got = {s: b for s, b in pool.map(get, symbols) if b}
    return ({s: {x.ts.date(): x.close for x in b} for s, b in got.items()},
            {s: {x.ts.date(): x.close * x.volume for x in b} for s, b in got.items()})


def by_turnover(p: "Prices", traded: dict, stocks: list, top: int = TOP) -> dict:
    """{month-end bar: the `top` most-traded stocks over the prior 6 months}, so a stock counts only
    once it was big at the time. Companies that failed are still missing, so bias is reduced, not gone."""
    out = {}
    for i in p.month_ends():
        window = p.days[max(0, i - 125):i + 1]
        scored = []
        for s in stocks:
            t = traded.get(s, {})
            vals = [t[d] for d in window if t.get(d)]
            if len(vals) >= 100:
                scored.append((statistics.median(vals), s))
        out[i] = [s for _, s in sorted(scored, reverse=True)[:top]]
    return out


def _brokerage(v: float) -> float:
    return max(5.0, min(20.0, v * 0.001))


def buy_cost(v: float) -> float:
    return v * (STT + EXCH + SEBI + STAMP + SLIP + GST * (EXCH + SEBI)) + _brokerage(v) * (1 + GST)


def sell_cost(v: float) -> float:
    return v * (STT + EXCH + SEBI + SLIP + GST * (EXCH + SEBI)) + (_brokerage(v) + DP) * (1 + GST)


class Prices:
    def __init__(self, closes: dict):
        self.days = sorted(closes[INDEX])
        self.series = {}
        for s, c in closes.items():
            last, filled = None, []
            for d in self.days:
                last = c.get(d, last)
                filled.append(last)
            self.series[s] = filled

    def month_ends(self) -> list:
        return [i for i in range(len(self.days) - 1) if self.days[i].month != self.days[i + 1].month]

    def at(self, s: str, i: int):
        return self.series[s][i]

    def ret(self, s: str, i: int, back: int, skip: int = 0):
        a, b = self.series[s][i - back], self.series[s][i - skip]
        return b / a - 1 if a and b else None


def _top(p: Prices, stocks: list, i: int, score, n: int = SLOTS) -> list:
    scored = [(score(s), s) for s in stocks if p.at(s, i - 252)]
    return [s for v, s in sorted((x for x in scored if x[0] is not None), reverse=True)[:n]]


def _momentum(p: Prices, stocks: list, i: int, n: int = SLOTS) -> list:
    return _top(p, stocks, i, lambda s: p.ret(s, i, 252, 21), n)


def _quarterly(p: Prices, stocks: list, i: int, held: list) -> list:
    """Fewer trades: only change the portfolio every third month."""
    return _momentum(p, stocks, i) if p.days[i].month % 3 == 0 or not held else held


def _buffered(p: Prices, stocks: list, i: int, held: list) -> list:
    """Fewer trades: keep a holding until it leaves the top 30, then fill from the top."""
    ranked = _momentum(p, stocks, i, 30)
    keep = [s for s in held if s in ranked]
    return keep + [s for s in ranked if s not in keep][:SLOTS - len(keep)]


def _vol(p: Prices, s: str, i: int):
    r = [p.series[s][k] / p.series[s][k - 1] - 1 for k in range(i - 251, i + 1) if p.series[s][k - 1]]
    return -statistics.pstdev(r) if len(r) > 200 else None


def _uptrend(p: Prices, i: int) -> bool:
    return p.at(INDEX, i) > statistics.mean(p.series[INDEX][i - 199:i + 1])


STRATEGIES = {
    "12-1 momentum": lambda p, st, i, held: _top(p, st, i, lambda s: p.ret(s, i, 252, 21)),
    "momentum, quarterly": lambda p, st, i, held: _quarterly(p, st, i, held),
    "momentum, keep until out of top 30": lambda p, st, i, held: _buffered(p, st, i, held),
    "momentum with market filter": lambda p, st, i, held: _top(p, st, i, lambda s: p.ret(s, i, 252, 21)) if _uptrend(p, i) else [],
    "near 52-week high": lambda p, st, i, held: _top(p, st, i, lambda s: p.at(s, i) / max(x for x in p.series[s][i - 251:i + 1] if x)),
    "low volatility": lambda p, st, i, held: _top(p, st, i, lambda s: _vol(p, s, i)),
    "1-month losers": lambda p, st, i, held: _top(p, st, i, lambda s: -p.ret(s, i, 21) if p.ret(s, i, 21) is not None else None),
    "Nifty ETF with 200-day filter": lambda p, st, i, held: [ETF] if _uptrend(p, i) else [],
}


def simulate(p: Prices, ends: list, stocks, rule, stats: dict = None) -> list:
    """Monthly portfolio values, after real charges on every change."""
    stats = {} if stats is None else stats
    cash, slots, values = CAPITAL, {}, []
    stats["changes"] = 0
    for k, i in enumerate(ends):
        if k:
            prev = ends[k - 1]
            slots = {s: v * (p.at(s, i) / p.at(s, prev) if p.at(s, prev) and p.at(s, i) else 1.0) for s, v in slots.items()}
            values.append(cash + sum(slots.values()))
        if k == len(ends) - 1:
            break
        picks = rule(p, stocks(i), i, list(slots))
        for s in [x for x in slots if x not in picks]:
            stats["changes"] += 1
            cash += max(0.0, slots[s] - sell_cost(slots[s]))
            del slots[s]
        new = [s for s in picks if s not in slots]
        if new:
            each = cash / len(new)
            for s in new:
                slots[s] = max(0.0, each - buy_cost(each))
            cash = 0.0
    return values


def equal_weight(p: Prices, ends: list, stocks: list) -> list:
    """Hold all stocks equally, reset monthly, with no charges: a deliberately kind benchmark."""
    value, out = CAPITAL, []
    for a, b in zip(ends, ends[1:]):
        r = [p.at(s, b) / p.at(s, a) - 1 for s in stocks(a) if p.at(s, a) and p.at(s, b)]
        value *= 1 + (sum(r) / len(r) if r else 0)
        out.append(value)
    return out


def _monthly(v: list) -> list:
    return [b / a - 1 if a else 0.0 for a, b in zip([CAPITAL] + v, v)]


def _cagr(v: list, start: float = CAPITAL) -> float:
    return ((v[-1] / start) ** (12 / len(v)) - 1) * 100 if v and v[-1] > 0 else -100.0


def _drawdown(v: list) -> float:
    peak, dd = CAPITAL, 0.0
    for x in v:
        peak = max(peak, x)
        dd = max(dd, 1 - x / peak)
    return dd * 100


def run(closes: dict, traded: dict = None) -> dict:
    p = Prices(closes)
    names = bhav.stocks_only(s for s in closes if s not in (ETF, INDEX))
    ends = [i for i in p.month_ends() if i > 260 and p.at(ETF, i)]
    members = by_turnover(p, traded, names) if traded else None
    stocks = (lambda i: members[i]) if members else (lambda i: names)
    ew = equal_weight(p, ends, stocks)
    etf = simulate(p, ends, stocks, lambda *_: [ETF])
    r_ew, r_etf = _monthly(ew), _monthly(etf)
    z = statistics.NormalDist().inv_cdf(1 - 0.025 / TESTS)
    half = len(ew) // 2
    rows = [{"name": "Equal-weight hold of the same stocks (no charges)", "cagr": _cagr(ew), "dd": _drawdown(ew), "final": ew[-1]},
            {"name": "Nifty ETF, buy and hold", "cagr": _cagr(etf), "dd": _drawdown(etf), "final": etf[-1]}]
    for name, rule in STRATEGIES.items():
        stats = {}
        v = simulate(p, ends, stocks, rule, stats)
        r = _monthly(v)
        ex = [a - b for a, b in zip(r, r_ew)]
        ex_etf = [a - b for a, b in zip(r, r_etf)]
        early, late = statistics.mean(ex[:half]) * 12 * 100, statistics.mean(ex[half:]) * 12 * 100
        low = (statistics.mean(ex) - z * statistics.stdev(ex) / len(ex) ** 0.5) * 12 * 100
        beats_etf = statistics.mean(ex_etf[:half]) > 0 and statistics.mean(ex_etf[half:]) > 0
        rows.append({"name": name, "cagr": _cagr(v), "dd": _drawdown(v), "final": v[-1], "sales": stats["changes"], "early": early, "late": late, "low": low,
                     "passed": early > 0 and late > 0 and low > 0 and beats_etf})
    return {"first": str(p.days[ends[0]]), "last": str(p.days[ends[-1]]), "months": len(ew), "stocks": len(names), "dynamic": bool(members), "rows": rows}


def to_markdown(rep: dict, note: str = "Companies that failed are missing from the data, so real results would be lower. Tax is not included.") -> str:
    L = ["# Delivery strategies", "",
         "%s to %s (%d months), %s, ₹50,000, 10 slots, monthly. Prices exclude dividends." % (
             rep["first"], rep["last"], rep["months"],
             "each month's 200 most-traded stocks from %d of today's Nifty 500" % rep["stocks"] if rep.get("dynamic")
             else "%d of today's Nifty 200 stocks" % rep["stocks"]),
         "", "**Passed: %s**" % (", ".join(r["name"] for r in rep["rows"] if r.get("passed")) or "none"), "",
         "| strategy | a year | worst fall | ₹50,000 became | stocks sold | vs equal-weight, early half | late half | lower bound | pass |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        if "early" in r:
            L.append("| %s | %+.1f%% | %.0f%% | ₹%.0f | %d | %+.1f%% | %+.1f%% | %+.1f%% | %s |" % (
                r["name"], r["cagr"], r["dd"], r["final"], r["sales"], r["early"], r["late"], r["low"], "yes" if r["passed"] else "no"))
        else:
            L.append("| %s | %+.1f%% | %.0f%% | ₹%.0f | | | | | benchmark |" % (r["name"], r["cagr"], r["dd"], r["final"]))
    L += ["", note, ""]
    return "\n".join(L)
