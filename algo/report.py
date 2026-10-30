"""End-of-day report and the permanent trade journal."""
from __future__ import annotations

import csv
import os

FIELDS = ["date", "symbol", "strategy", "qty", "entry_price", "exit_price", "entry_ts", "exit_ts",
          "exit_reason", "gross_pnl", "charges", "net_pnl", "planned_risk", "r_multiple"]


def expected_ticks(cfg: dict) -> int:
    """Scheduled ticks in a full session: one per bar from the entry window's start to the last bar."""
    def mins(hm):
        h, m = hm.split(":")
        return int(h) * 60 + int(m)
    return (mins(cfg["session_close"]) - mins(cfg["entry_window"][0])) // cfg["bar_minutes"]


def daily_markdown(state: dict, cfg: dict) -> str:
    t, d = state["today"], state["date"]
    trades = t["trades"]
    L = ["# %s — paper trading" % d, "",
         "Net P&L **₹%+.2f** on %d trade(s). Equity ₹%.2f (started ₹%s)." % (
             t["realised"], len(trades), state["equity"], cfg["capital"]),
         "Schedule: %d of %d ticks ran." % (t.get("ticks", 0), expected_ticks(cfg)), ""]
    if trades:
        L += ["| symbol | strategy | qty | entry | exit | reason | gross ₹ | charges ₹ | net ₹ | R |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for x in trades:
            L.append("| %s | %s | %d | %.2f | %.2f | %s | %+.2f | %.2f | %+.2f | %+.2f |" % (
                x["symbol"], x["strategy"], x["qty"], x["entry_price"], x["exit_price"], x["exit_reason"],
                x["gross_pnl"], x["charges"], x["net_pnl"], x["r_multiple"]))
        L.append("")
    if state["positions"]:
        L += ["**Still open (should be flat — investigate):** " + ", ".join(sorted(state["positions"])), ""]
    kinds = {}
    for e in t["events"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    L += ["Events: " + (", ".join("%s %d" % kv for kv in sorted(kinds.items())) or "none"), "",
          "## Log", ""]
    L += ["- %s %s %s: %s" % (e["time"], e["kind"], e["symbol"], e["msg"]) for e in t["events"]] or ["- (quiet day)"]
    L.append("")
    return "\n".join(L)


def append_journal(path: str, date: str, trades: list) -> int:
    if not trades:
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = set()
    if os.path.exists(path):
        with open(path, newline="") as fh:
            existing = {(r["date"], r["symbol"], r["entry_ts"]) for r in csv.DictReader(fh)}
    new = [dict(x, date=date) for x in trades if (date, x["symbol"], x["entry_ts"]) not in existing]
    write_header = not os.path.exists(path)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerows(new)
    return len(new)
