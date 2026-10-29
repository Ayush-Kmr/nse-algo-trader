"""Telegram alerts, only if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set. Never raises."""
from __future__ import annotations

import json
import os
import urllib.request


def telegram(text: str) -> bool:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    body = json.dumps({"chat_id": chat, "text": text[:4000]}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % token, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).close()
        return True
    except Exception as e:  # noqa: BLE001 - alerts must never break trading
        print("telegram failed: %s" % e)
        return False


def event_notifier(ev: dict) -> None:
    telegram("[PAPER] %s %s %s: %s" % (ev["time"], ev["kind"], ev["symbol"], ev["msg"]))
