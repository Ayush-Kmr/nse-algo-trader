import json
import os
from datetime import date, datetime, timedelta

from algo.models import Bar
from algo.timeutil import IST

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cfg(**overrides):
    with open(os.path.join(ROOT, "config.json")) as fh:
        c = json.load(fh)
    c.update(overrides)
    return c


def at(d: date, hm: str) -> datetime:
    h, m = hm.split(":")
    return datetime(d.year, d.month, d.day, int(h), int(m), tzinfo=IST)


def day(d: date, ohlcv: list, start="09:15") -> list:
    """ohlcv: [(o, h, l, c, v), ...] as consecutive 5-minute bars from `start`."""
    t0 = at(d, start)
    return [Bar(t0 + timedelta(minutes=5 * i), *map(float, row)) for i, row in enumerate(ohlcv)]


def flat(price, n, vol=1000):
    return [(price, price + 0.5, price - 0.5, price, vol)] * n


D = date(2026, 10, 27)  # a Tuesday
