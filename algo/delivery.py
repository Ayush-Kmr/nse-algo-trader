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

from . import data

CAPITAL, SLOTS = 50000.0, 10
ETF, INDEX = "NIFTYBEES", "^NSEI"
STT, EXCH, SEBI, STAMP, GST, DP, SLIP = 0.001, 0.000030699, 0.000001, 0.00015, 0.18, 20.0, 0.0006
TESTS = 6


def fetch(symbols: list) -> dict:
    def get(s):
        try:
            return s, {b.ts.date(): b.close for b in data.fetch_bars(s, "20y", "1d", retries=2, timeout=30)}
        except Exception:  # noqa: BLE001 - a missing stock narrows the test, it does not stop it
            return s, None
    with ThreadPoolExecutor(max_workers=6) as pool:
        return {s: c for s, c in pool.map(get, symbols) if c}


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


def _top(p: Prices, stocks: list, i: int, score) -> list:
    scored = [(score(s), s) for s in stocks if p.at(s, i - 252)]
    return [s for v, s in sorted((x for x in scored if x[0] is not None), reverse=True)[:SLOTS]]


def _vol(p: Prices, s: str, i: int):
    r = [p.series[s][k] / p.series[s][k - 1] - 1 for k in range(i - 251, i + 1) if p.series[s][k - 1]]
    return -statistics.pstdev(r) if len(r) > 200 else None


def _uptrend(p: Prices, i: int) -> bool:
    return p.at(INDEX, i) > statistics.mean(p.series[INDEX][i - 199:i + 1])


STRATEGIES = {
    "12-1 momentum": lambda p, st, i: _top(p, st, i, lambda s: p.ret(s, i, 252, 21)),
    "momentum with market filter": lambda p, st, i: _top(p, st, i, lambda s: p.ret(s, i, 252, 21)) if _uptrend(p, i) else [],
    "near 52-week high": lambda p, st, i: _top(p, st, i, lambda s: p.at(s, i) / max(x for x in p.series[s][i - 251:i + 1] if x)),
    "low volatility": lambda p, st, i: _top(p, st, i, lambda s: _vol(p, s, i)),
    "1-month losers": lambda p, st, i: _top(p, st, i, lambda s: -p.ret(s, i, 21) if p.ret(s, i, 21) is not None else None),
    "Nifty ETF with 200-day filter": lambda p, st, i: [ETF] if _uptrend(p, i) else [],
}


def simulate(p: Prices, ends: list, stocks: list, rule) -> list:
    """Monthly portfolio values, after real charges on every change."""
    cash, slots, values = CAPITAL, {}, []
    for k, i in enumerate(ends):
        if k:
            prev = ends[k - 1]
            slots = {s: v * (p.at(s, i) / p.at(s, prev) if p.at(s, prev) and p.at(s, i) else 1.0) for s, v in slots.items()}
            values.append(cash + sum(slots.values()))
        if k == len(ends) - 1:
            break
        picks = rule(p, stocks, i)
        for s in [x for x in slots if x not in picks]:
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
        r = [p.at(s, b) / p.at(s, a) - 1 for s in stocks if p.at(s, a) and p.at(s, b)]
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


def run(closes: dict) -> dict:
    p = Prices(closes)
    stocks = [s for s in closes if s not in (ETF, INDEX)]
    ends = [i for i in p.month_ends() if i > 260 and p.at(ETF, i)]
    ew = equal_weight(p, ends, stocks)
    etf = simulate(p, ends, stocks, lambda *_: [ETF])
    r_ew, r_etf = _monthly(ew), _monthly(etf)
    z = statistics.NormalDist().inv_cdf(1 - 0.025 / TESTS)
    half = len(ew) // 2
    rows = [{"name": "Equal-weight hold of the same stocks (no charges)", "cagr": _cagr(ew), "dd": _drawdown(ew), "final": ew[-1]},
            {"name": "Nifty ETF, buy and hold", "cagr": _cagr(etf), "dd": _drawdown(etf), "final": etf[-1]}]
    for name, rule in STRATEGIES.items():
        v = simulate(p, ends, stocks, rule)
        r = _monthly(v)
        ex = [a - b for a, b in zip(r, r_ew)]
        ex_etf = [a - b for a, b in zip(r, r_etf)]
        early, late = statistics.mean(ex[:half]) * 12 * 100, statistics.mean(ex[half:]) * 12 * 100
        low = (statistics.mean(ex) - z * statistics.stdev(ex) / len(ex) ** 0.5) * 12 * 100
        beats_etf = statistics.mean(ex_etf[:half]) > 0 and statistics.mean(ex_etf[half:]) > 0
        rows.append({"name": name, "cagr": _cagr(v), "dd": _drawdown(v), "final": v[-1], "early": early, "late": late, "low": low,
                     "passed": early > 0 and late > 0 and low > 0 and beats_etf})
    return {"first": str(p.days[ends[0]]), "last": str(p.days[ends[-1]]), "months": len(ew), "stocks": len(stocks), "rows": rows}


def to_markdown(rep: dict) -> str:
    L = ["# Delivery strategies", "",
         "%s to %s (%d months), %d of today's Nifty 200 stocks, ₹50,000, 10 slots, monthly. Prices exclude dividends." % (
             rep["first"], rep["last"], rep["months"], rep["stocks"]),
         "", "**Passed: %s**" % (", ".join(r["name"] for r in rep["rows"] if r.get("passed")) or "none"), "",
         "| strategy | a year | worst fall | ₹50,000 became | vs equal-weight, early half | late half | lower bound | pass |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        if "early" in r:
            L.append("| %s | %+.1f%% | %.0f%% | ₹%.0f | %+.1f%% | %+.1f%% | %+.1f%% | %s |" % (
                r["name"], r["cagr"], r["dd"], r["final"], r["early"], r["late"], r["low"], "yes" if r["passed"] else "no"))
        else:
            L.append("| %s | %+.1f%% | %.0f%% | ₹%.0f | | | | benchmark |" % (r["name"], r["cagr"], r["dd"], r["final"]))
    L += ["", "All of this uses today's winners, so real results would be lower. Tax on gains is not included.", ""]
    return "\n".join(L)
