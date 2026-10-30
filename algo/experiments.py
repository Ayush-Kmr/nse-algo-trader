"""Run a fixed list of config variants over the SAME cached history and compare them.

Rules that keep this honest:
- Variants are written down in experiments.json BEFORE looking at results.
- A variant is chosen on IN-SAMPLE only; out-of-sample is the confirmation, never the selector.
- Everything is net of costs.
"""
from __future__ import annotations

import copy
import json

from . import backtest as bt


def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def run_all(cfg: dict, history: dict, variants: list, exclude_date=None) -> list:
    index = cfg["regime"]["index"]
    rows = []
    for v in variants:
        c = deep_merge(cfg, v.get("set", {}))
        rep = bt.split_report(bt.run(c, history, index, exclude_date), tests=len(variants))
        rows.append({"name": v["name"], "idea": v.get("idea", ""), "report": rep})
    return rows


def _cell(m: dict) -> str:
    if not m.get("trades"):
        return "0 | | | |"
    return "%d | %.1f | %+.2f | %+.3f" % (m["trades"], m["win_rate_pct"], m["expectancy_rs"], m["avg_r_net"])


def to_markdown(rows: list, rep0: dict) -> str:
    L = ["# Experiments", "",
         "Data %s to %s (%d sessions). In-sample before %s, out-of-sample from it. All figures net of costs." % (
             rep0["first_day"], rep0["last_day"], rep0["days"], rep0["oos_from"]),
         "Pick on **in-sample** ₹/trade; read out-of-sample only as confirmation.", "",
         "Gate: 30+ out-of-sample trades and a lower bound on avg R above zero, corrected for %d variants." % len(rows), "",
         "| variant | IS trades | IS win% | IS ₹/trade | IS avg R | OOS trades | OOS win% | OOS ₹/trade | OOS avg R | all net ₹ | charges ₹ | gate |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rep = r["report"]
        a = rep["all"]
        L.append("| %s | %s | %s | %s | %s | %s |" % (
            r["name"], _cell(rep["in_sample"]), _cell(rep["out_of_sample"]),
            "%+.2f" % a["net_total"] if a.get("trades") else "0",
            "%.2f" % a["charges_total"] if a.get("trades") else "0",
            rep["verdict"].split()[0].rstrip(":")))
    L += ["", "## Ideas", ""]
    L += ["- **%s**: %s" % (r["name"], r["idea"]) for r in rows]
    L.append("")
    return "\n".join(L)


def load_variants(path: str) -> list:
    with open(path) as fh:
        return json.load(fh)["variants"]
