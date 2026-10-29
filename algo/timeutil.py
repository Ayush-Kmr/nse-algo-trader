from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

# India has no DST, so a fixed offset is exact.
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    return datetime.now(IST)


def hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def parse_now(s: str) -> datetime:
    """'2026-10-29 10:15' (IST) -> aware datetime."""
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=IST)


def is_trading_day(d: date, holidays) -> bool:
    return d.weekday() < 5 and d.isoformat() not in set(holidays)
