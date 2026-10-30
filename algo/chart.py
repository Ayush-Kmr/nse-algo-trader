"""Chart images for Telegram alerts, drawn with the standard library so ticks stay fast.

A falling-back alert must never lose the message: if drawing or sending fails, the text still goes.
"""
from __future__ import annotations

import struct
import zlib
from datetime import datetime, timedelta

from .notify import format_event, send_photo, telegram

W, H = 960, 560
LEFT, RIGHT, TOP, BOTTOM = 16, 118, 74, 34
BG = (17, 24, 28)
GRID = (42, 54, 60)
TEXT = (232, 238, 234)
MUTED = (157, 176, 179)
UP = (60, 194, 173)
DOWN = (240, 132, 108)
ENTRY = (159, 180, 245)
AMBER = (233, 187, 98)

FONT = {
    "0": "0E 11 13 15 19 11 0E", "1": "04 0C 04 04 04 04 0E", "2": "0E 11 01 02 04 08 1F",
    "3": "1F 02 04 02 01 11 0E", "4": "02 06 0A 12 1F 02 02", "5": "1F 10 1E 01 01 11 0E",
    "6": "06 08 10 1E 11 11 0E", "7": "1F 01 02 04 08 08 08", "8": "0E 11 11 0E 11 11 0E",
    "9": "0E 11 11 0F 01 02 0C", "A": "0E 11 11 1F 11 11 11", "B": "1E 11 11 1E 11 11 1E",
    "C": "0E 11 10 10 10 11 0E", "D": "1C 12 11 11 11 12 1C", "E": "1F 10 10 1E 10 10 1F",
    "F": "1F 10 10 1E 10 10 10", "G": "0E 11 10 17 11 11 0F", "H": "11 11 11 1F 11 11 11",
    "I": "0E 04 04 04 04 04 0E", "J": "07 02 02 02 02 12 0C", "K": "11 12 14 18 14 12 11",
    "L": "10 10 10 10 10 10 1F", "M": "11 1B 15 15 11 11 11", "N": "11 11 19 15 13 11 11",
    "O": "0E 11 11 11 11 11 0E", "P": "1E 11 11 1E 10 10 10", "Q": "0E 11 11 11 15 12 0D",
    "R": "1E 11 11 1E 14 12 11", "S": "0F 10 10 0E 01 01 1E", "T": "1F 04 04 04 04 04 04",
    "U": "11 11 11 11 11 11 0E", "V": "11 11 11 11 11 0A 04", "W": "11 11 11 15 15 15 0A",
    "X": "11 11 0A 04 0A 11 11", "Y": "11 11 11 0A 04 04 04", "Z": "1F 01 02 04 08 10 1F",
    ".": "00 00 00 00 00 0C 0C", ":": "00 0C 0C 00 0C 0C 00", "+": "00 04 04 1F 04 04 00",
    "-": "00 00 00 1F 00 00 00", "%": "18 19 02 04 08 13 03", "(": "02 04 08 08 08 04 02",
    ")": "08 04 02 02 02 04 08", ",": "00 00 00 00 0C 04 08", "/": "00 01 02 04 08 10 00",
}


class Canvas:
    def __init__(self):
        self.px = bytearray(bytes(BG) * (W * H))

    def rect(self, x0: int, y0: int, x1: int, y1: int, c: tuple) -> None:
        x0, x1 = max(0, min(x0, x1)), min(W, max(x0, x1) + 1)
        y0, y1 = max(0, min(y0, y1)), min(H, max(y0, y1) + 1)
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * W + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, y: int, x0: int, x1: int, c: tuple, dash: int = 0) -> None:
        for x in range(x0, x1, dash * 2 or x1 - x0):
            self.rect(x, y, x + (dash or x1 - x0) - 1, y + 1, c)

    def text(self, x: int, y: int, s: str, c: tuple, scale: int = 2) -> None:
        for ch in s.upper():
            rows = FONT.get(ch)
            if rows:
                for j, row in enumerate(rows.split()):
                    bits = int(row, 16)
                    for i in range(5):
                        if bits & (16 >> i):
                            self.rect(x + i * scale, y + j * scale, x + (i + 1) * scale - 1, y + (j + 1) * scale - 1, c)
            x += 6 * scale

    def marker(self, x: int, y: int, c: tuple) -> None:
        self.rect(x - 7, y - 7, x + 7, y + 7, BG)
        self.rect(x - 5, y - 5, x + 5, y + 5, c)

    def png(self) -> bytes:
        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        raw = b"".join(b"\0" + bytes(self.px[y * W * 3:(y + 1) * W * 3]) for y in range(H))
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def render(bars: list, title: str, subtitle: str, levels: list, marks: list, tag: str = "PAPER") -> bytes:
    """levels: [(label, price, colour)]. marks: [(bar start, price, colour)]. Up to 15:30 on a fixed axis."""
    c = Canvas()
    c.text(LEFT, 12, title, TEXT, 3)
    c.text(LEFT, 44, subtitle, MUTED, 2)
    c.text(W - 12 * len(tag) - 14, 14, tag, AMBER, 2)
    prices = [p for b in bars for p in (b.high, b.low)] + [lv[1] for lv in levels]
    lo, hi = min(prices), max(prices)
    pad = max((hi - lo) * 0.08, hi * 0.001)
    lo, hi = lo - pad, hi + pad
    plot_w, plot_h = W - LEFT - RIGHT, H - TOP - BOTTOM
    y = lambda p: int(TOP + (hi - p) * plot_h / (hi - lo))  # noqa: E731
    t0 = bars[0].ts.replace(hour=9, minute=15, second=0, microsecond=0)
    slots = 75
    x = lambda ts: LEFT + int(((ts - t0).total_seconds() / 300 + 0.5) * plot_w / slots)  # noqa: E731
    body = max(3, int(plot_w / slots * 0.66))
    for i in range(5):
        c.hline(TOP + i * plot_h // 4, LEFT, W - RIGHT, GRID)
    for hhmm in ("09:15", "11:00", "13:00", "15:15"):
        ts = t0 + timedelta(minutes=int(hhmm[:2]) * 60 + int(hhmm[3:]) - 555)
        c.text(min(x(ts) - 14, W - RIGHT - 60), H - 24, hhmm, MUTED, 2)
    for label, price, colour in levels:
        c.hline(y(price), LEFT, W - RIGHT, colour, dash=8)
        c.text(W - RIGHT + 8, y(price) - 15, label, colour, 2)
        c.text(W - RIGHT + 8, y(price) + 2, "%.2f" % price, colour, 2)
    for b in bars:
        colour = UP if b.close >= b.open else DOWN
        cx = x(b.ts)
        c.rect(cx, y(b.high), cx + 1, y(b.low), colour)
        c.rect(cx - body // 2, y(max(b.open, b.close)), cx - body // 2 + body, y(min(b.open, b.close)) + 1, colour)
    for ts, price, colour in marks:
        c.marker(x(ts), y(price), colour)
    return c.png()


def alert_image(ev: dict, bars: list, tag: str = "PAPER") -> bytes:
    d = ev.get("data", {})
    if ev["kind"] == "ENTRY":
        s = d["signal"]
        entry, stop, target = d["fill"], s["stop"], s["target"]
        title = "%s BUY %d AT %.2f" % (ev["symbol"], d["qty"], entry)
        subtitle = "RISK RS %.2f  -  ALERT AT %s" % (d["loss_at_stop"], ev["time"])
        marks = [(datetime.fromisoformat(d["entry_ts"]), entry, ENTRY)]
    else:
        t = d["trade"]
        entry, stop, target = t["entry_price"], d["stop"], d["target"]
        reason = t["exit_reason"].upper()
        title = "%s %s AT %.2f" % (ev["symbol"], reason, t["exit_price"])
        subtitle = "NET RS %+.2f  (%+.2fR)  -  CHARGES RS %.2f" % (t["net_pnl"], t["r_multiple"], t["charges"])
        out = max((b for b in bars if b.end <= datetime.fromisoformat(t["exit_ts"])), key=lambda b: b.ts, default=bars[-1])
        marks = [(datetime.fromisoformat(t["entry_ts"]), entry, ENTRY), (out.ts, t["exit_price"], UP if t["net_pnl"] > 0 else DOWN)]
    return render(bars, title, subtitle, [("TARGET", target, UP), ("ENTRY", entry, ENTRY), ("STOP", stop, DOWN)], marks, tag)


WHY = {"orb": "price closed above the opening range", "vwap_reclaim": "price closed back above VWAP"}
EXITS = {"stop": "Stop hit", "stop (gap)": "Stop hit on a gap", "target": "Target hit", "target (gap)": "Target hit on a gap",
         "trail stop": "Trailing stop hit", "trail stop (gap)": "Trailing stop hit on a gap", "square-off": "15:15 square-off"}


def caption(ev: dict) -> str:
    """The alert in plain words, to sit under the chart. Paper alerts are never recommendations."""
    d = ev.get("data", {})
    if ev["kind"] == "ENTRY" and "signal" in d:
        s = d["signal"]
        return ("🟢 ENTRY: %s at %s\nWhy: %s\nBuy %d at %.2f\nStop %.2f (exit here if it falls)\nTarget %.2f\n"
                "Paper risk ₹%.2f, charges included\n\nPaper alert, not a recommendation." % (
                    ev["symbol"], ev["time"], WHY.get(ev["msg"].split(":")[0], "strategy signal"), d["qty"], d["fill"],
                    s["stop"], s["target"], d["loss_at_stop"]))
    if ev["kind"] == "EXIT" and "trade" in d:
        t = d["trade"]
        return ("🔵 EXIT: %s at %s\n%s\nSold %d at %.2f (bought at %.2f)\nNet ₹%+.2f after ₹%.2f charges (%+.2fR)\n\n"
                "This reports what already happened." % (
                    ev["symbol"], ev["time"], EXITS.get(t["exit_reason"], t["exit_reason"]), t["qty"], t["exit_price"],
                    t["entry_price"], t["net_pnl"], t["charges"], t["r_multiple"]))
    return format_event(ev)


def chart_notifier(bars_by_symbol: dict, tag: str = "PAPER", prefix: str = ""):
    """Entries and exits go out as a chart with a plain-words caption; everything else as text."""
    def notify(ev: dict) -> None:
        text = prefix + caption(ev)
        bars = bars_by_symbol.get(ev["symbol"])
        if ev["kind"] in ("ENTRY", "EXIT") and bars:
            try:
                if send_photo(alert_image(ev, bars, tag), text):
                    return
            except Exception as e:  # noqa: BLE001 - an alert must never be lost to a drawing bug
                print("chart failed: %s" % type(e).__name__)
        telegram(text)
    return notify
