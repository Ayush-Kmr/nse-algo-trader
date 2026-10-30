"""Telegram alerts to a chat or channel, only if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.

TELEGRAM_CHAT_ID is a numeric id (-100... for a channel) or a public channel's @name. To post in a
channel the bot must be an admin of it with "Post Messages". send() never raises.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Tuple

ICONS = {"ENTRY": "🟢", "EXIT": "🔵", "CRITICAL": "🚨", "WARN": "⚠️", "GAP": "⚠️", "KILL": "🛑", "START": "▶️"}


def send(text: str) -> Tuple[bool, str]:
    """-> (delivered, reason). The reason never contains the token."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False, "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set"
    body = json.dumps({"chat_id": chat, "text": text[:4000]}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % token, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).close()
        return True, "sent"
    except urllib.error.HTTPError as e:
        try:
            why = json.loads(e.read().decode("utf-8")).get("description", "")
        except ValueError:
            why = ""
        return False, "HTTP %s %s" % (e.code, why)
    except Exception as e:  # noqa: BLE001 - alerts must never break trading
        return False, type(e).__name__


def telegram(text: str) -> bool:
    ok, why = send(text)
    if not ok and "not set" not in why:
        print("telegram failed: %s" % why)
    return ok


def format_event(ev: dict) -> str:
    return "%s [PAPER] %s %s %s: %s" % (ICONS.get(ev["kind"], "•"), ev["time"], ev["kind"], ev["symbol"], ev["msg"])


def event_notifier(ev: dict) -> None:
    telegram(format_event(ev))
