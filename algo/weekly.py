"""The weekly learning run: refit on the newest data, read the system's own paper trades, and report.

It learns and reports only. Nothing here changes config.json or what the engine trades: a change
needs the gate in README.md, then a person's decision.
"""
from __future__ import annotations

import csv
import os

from . import backtest as bt
from . import experiments as ex
from . import learn, longtest, research


def paper_results(path: str) -> dict:
    if not os.path.exists(path):
        return {"trades": 0}
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in ("net_pnl", "gross_pnl", "charges", "r_multiple"):
            r[k] = float(r[k])
    return bt.metrics(rows)


def message(short: dict, long_rep: dict, paper: dict) -> str:
    passed = "PASSES" in short["verdict"] or "PASSES" in long_rep["verdict"]
    lines = ["🧠 [PAPER] Weekly learning report", "",
             "5-minute data, %d signals: %+.2fR before charges, model picked %d" % (
                 short["signals"], short["unseen"].get("avg_gross_r", 0), short["picked"]["signals"]),
             "Hourly data, %d sessions, %d signals: %+.2fR before charges, model picked %d" % (
                 long_rep["sessions"], long_rep["all"]["signals"], long_rep["all"].get("avg_gross_r", 0), long_rep["picked"]["signals"])]
    if paper.get("trades"):
        lines.append("Own paper trades: %d, net ₹%+.2f, avg %+.3fR" % (paper["trades"], paper["net_total"], paper["avg_r_net"]))
    else:
        lines.append("Own paper trades: none yet")
    lines += ["", "Result: a candidate passed. Review before any change." if passed else
              "Result: nothing passed, so the strategies stay unchanged. No proven edge yet."]
    return "\n".join(lines)


def run(cfg: dict, history: dict, universe: list, journal: str, exclude_date) -> tuple:
    short = learn.run(cfg, history, exclude_date)
    hourly = longtest.fetch(universe + [cfg["regime"]["index"]])
    long_rep = longtest.report(longtest.rows(cfg, hourly, exclude_date))
    return short, long_rep, paper_results(journal)
