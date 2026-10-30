"""Read-only slash commands from the Telegram channel.

Nothing runs between ticks, so commands are collected at the start of every tick and end-of-day run:
replies take up to 5 minutes in market hours. Telegram keeps unread updates for 24 hours. Only posts
from TELEGRAM_CHAT_ID are answered, and no command can change anything. Never raises.
"""
from __future__ import annotations

import json
import os
import urllib.request

from .notify import telegram
from .report import expected_ticks

HELP = ("Commands (paper trading, replies within 5 minutes in market hours):\n"
        "/status - equity, today's P&L, open positions, kill switch\n"
        "/positions - open positions with stop and target\n"
        "/trades - today's closed trades\n"
        "/pnl - total P&L and the last 5 days\n"
        "/schedule - ticks that ran today\n"
        "/help - this list")


def _status(state, cfg, kill):
    t = state["today"]
    return "📈 %s (%s)\nEquity ₹%.2f\nToday net ₹%+.2f on %d trade(s)\nOpen positions: %d\nKill switch: %s" % (
        state.get("date") or "no session yet", cfg["mode"], state["equity"], t["realised"], len(t["trades"]),
        len(state["positions"]), "ON" if kill else "off")


def _positions(state, cfg, kill):
    if not state["positions"]:
        return "No open positions."
    return "\n".join("%s %s: %d @ %.2f, stop %.2f, target %.2f" % (
        p["symbol"], p["strategy"], p["qty"], p["entry_price"], p["stop"], p["target"])
        for p in state["positions"].values())


def _trades(state, cfg, kill):
    trades = state["today"]["trades"]
    if not trades:
        return "No closed trades today."
    return "\n".join("%s %s: %d, %.2f to %.2f, %s, net ₹%+.2f (%+.2fR)" % (
        x["symbol"], x["strategy"], x["qty"], x["entry_price"], x["exit_price"], x["exit_reason"],
        x["net_pnl"], x["r_multiple"]) for x in trades)


def _pnl(state, cfg, kill):
    days = sorted(state.get("history", {}).items())[-5:]
    lines = ["Total ₹%+.2f (equity ₹%.2f, started ₹%s)" % (
        state["equity"] - cfg["capital"], state["equity"], cfg["capital"])]
    lines += ["%s: ₹%+.2f on %d trade(s)" % (d, r["net"], r["trades"]) for d, r in days]
    return "\n".join(lines)


def _schedule(state, cfg, kill):
    t = state["today"]
    return "%s: %d of %d ticks ran, last at %s" % (
        state.get("date") or "no session yet", t.get("ticks", 0), expected_ticks(cfg),
        (t.get("last_tick") or "never")[11:16] or "never")


COMMANDS = {"status": _status, "positions": _positions, "trades": _trades, "pnl": _pnl,
            "schedule": _schedule, "help": lambda s, c, k: HELP, "start": lambda s, c, k: HELP}


def answer(text: str, state: dict, cfg: dict, kill: bool):
    """-> the reply, or None when the text is not a command. '/status@SomeBot' also works."""
    text = text.strip()
    if not text.startswith("/"):
        return None
    name = text.split()[0][1:].split("@")[0].lower()
    fn = COMMANDS.get(name)
    return fn(state, cfg, kill) if fn else "Unknown command. Send /help."


def _get_updates(token: str, offset=None) -> list:
    body = {"timeout": 0, "allowed_updates": ["channel_post", "message"]}
    if offset is not None:
        body["offset"] = offset
    req = urllib.request.Request("https://api.telegram.org/bot%s/getUpdates" % token,
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8")).get("result", [])


def process(state: dict, cfg: dict, kill: bool) -> int:
    """Answer waiting commands, then mark them read. -> how many were answered."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return 0
    answered = 0
    try:
        updates = _get_updates(token)
        for u in updates:
            msg = u.get("channel_post") or u.get("message") or {}
            c = msg.get("chat") or {}
            if chat not in (str(c.get("id")), "@%s" % c.get("username")):
                continue
            reply = answer(msg.get("text") or "", state, cfg, kill)
            if reply:
                telegram(reply)
                answered += 1
        if updates:
            _get_updates(token, updates[-1]["update_id"] + 1)
    except Exception as e:  # noqa: BLE001 - commands must never break trading
        print("telegram commands failed: %s" % type(e).__name__)
    return answered
