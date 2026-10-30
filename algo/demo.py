"""A labelled walk-through of the channel's messages, using a made-up stock.

Every message says DEMO, and the symbol is EXAMPLE so that none can be mistaken for a real signal.
The alert lines use the same formatter as real alerts.
"""
from __future__ import annotations

import time

from .notify import format_event, telegram

TAG = "🧪 DEMO, NOT A REAL TRADE\n\n"


def _ev(t: str, kind: str, symbol: str, msg: str) -> str:
    return format_event({"time": t, "kind": kind, "symbol": symbol, "msg": msg})


MESSAGES = [
    "This is a walk-through of what this channel sends. EXAMPLE is a made-up stock and every number "
    "is invented.\n\nThis system is paper trading. It has lost money in every test so far, so no "
    "alert is a recommendation.",

    "1. MORNING CHECK\n\n" + _ev("09:32", "START", "*", "engine live, equity 50000.00") +
    "\n\nThis means ticks are running. If it has not appeared by about 09:45, the system is not "
    "running that day, so do not rely on the channel.",

    "2. ENTRY ALERT\n\n" + _ev("10:02", "ENTRY", "EXAMPLE",
                               "orb: buy 24 @ 1158.25, stop 1150.35, target 1181.75, risk 244.24, RS +0.42% (closed 1157.60 above range)") +
    "\n\nHow to read it:\n- orb: the strategy\n- buy 24 @ 1158.25: paper quantity and price\n"
    "- stop 1150.35: where the trade is wrong\n- target 1181.75: where it takes profit\n"
    "- risk 244.24: rupees lost at the stop, charges included\n\n"
    "The quantity assumes ₹50,000 of capital and Angel One charges. It is not sized for your account.",

    "3. IF YOU CHOOSE TO COPY A TRADE ON GROWW\n\nThis is how the system's own rules translate to a "
    "manual order. Check each step in the app first, because screens and order types can change.\n\n"
    "1. Compare the live price with the alert. The system drops a trade more than 0.3% above the "
    "alert price (here, above about 1161.70).\n2. Choose intraday, not delivery.\n3. Use a limit "
    "order, with your own quantity.\n4. Place the stop as soon as the buy fills. Do not wait for an "
    "EXIT alert.\n5. Place the target, or watch the position if the app will not hold both.\n"
    "6. Be flat by 15:15, even with no alert.",

    "4. EXIT ALERT: STOP HIT\n\n" + _ev("11:50", "EXIT", "EXAMPLE",
                                        "stop 24 @ 1149.75, net -245.34 (-1.00R, charges 56.94)") +
    "\n\nThis is a report of what already happened on paper. It can arrive minutes late, which is "
    "why a stop must already be in place. Losses like this are normal: about 2 in 3 test trades lost.",

    "5. EXIT ALERT: TARGET HIT\n\n" + _ev("13:20", "EXIT", "EXAMPLE",
                                          "target 24 @ 1181.75, net +506.12 (+2.07R, charges 57.88)") +
    "\n\nExits at the target were rare in the portfolio backtest: 1 of 71 trades in the first report.",

    "6. EXIT ALERT: 15:15 SQUARE-OFF\n\n" + _ev("15:17", "EXIT", "EXAMPLE",
                                                "square-off 24 @ 1163.40, net +66.71 (+0.27R, charges 56.89)") +
    "\n\nAnything still open is closed. Do not hold an intraday trade waiting for this message.",

    "7. WARNINGS\n\n" + _ev("11:22", "GAP", "*", "no tick for 25 minutes: the schedule is running late") +
    "\n\n" + _ev("12:05", "WARN", "EXAMPLE", "no data for an open position: it is not being managed") +
    "\n\nAfter either one, the channel can no longer be trusted to report on time. Manage any real "
    "position yourself.",

    "8. END OF DAY\n\n📊 [PAPER] 2026-11-02: net ₹-245.34 on 1 trade(s), equity ₹49754.66, 72/72 ticks ran"
    "\n\nThe tick count shows how much of the day was monitored.",

    "9. COMMANDS\n\nType these here: /status /positions /trades /pnl /schedule /help\n\nReplies come "
    "at the next tick, up to 5 minutes in market hours. Outside them, they can be hours late.\n\n"
    "End of demo. Real paper alerts begin on the next trading day, and they will not say DEMO.",
]


def run(pause: float = 1.2) -> int:
    sent = 0
    for m in MESSAGES:
        sent += 1 if telegram(TAG + m) else 0
        time.sleep(pause)
    return sent
