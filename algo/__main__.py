"""python -m algo tick | eod | backtest | experiments | signals | walkforward | status | commands | telegram-test"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import backtest as bt
from . import commands
from . import experiments as ex
from . import research
from .data import YahooSource, load_history, save_history
from .engine import Engine, new_state
from .notify import event_notifier, send, telegram
from .report import append_journal, daily_markdown, expected_ticks
from .timeutil import hhmm, is_trading_day, now_ist, parse_now

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "state.json")


def load_cfg(path: str) -> dict:
    with open(path) as fh:
        cfg = json.load(fh)
    if cfg.get("mode") not in ("READ_ONLY", "PAPER"):
        sys.exit("mode %r is not allowed: only READ_ONLY and PAPER exist." % cfg.get("mode"))
    return cfg


def load_state(cfg: dict) -> dict:
    if os.path.exists(STATE):
        with open(STATE) as fh:
            return json.load(fh)
    return new_state(cfg)


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=1)
    os.replace(tmp, STATE)


def kill_switch_on() -> bool:
    return os.environ.get("KILL_SWITCH", "").strip().lower() in ("1", "true", "on", "yes")


def cmd_tick(a, cfg) -> int:
    now = parse_now(a.now) if a.now else now_ist()
    state = load_state(cfg)
    if not a.quiet:
        commands.process(state, cfg, kill_switch_on())
    if not is_trading_day(now.date(), cfg["holidays"]):
        print("%s: not a trading day." % now.date())
        return 0
    if not (hhmm(cfg["session_open"]) <= now.time() <= hhmm(cfg["session_close"])):
        print("%s IST: market closed, nothing to do." % now.strftime("%H:%M"))
        return 0

    index = cfg["regime"]["index"]
    bars, errors = YahooSource().today(cfg["universe"] + [index], now, cfg.get("bar_grace_seconds", 0))
    index_bars = bars.pop(index, None)
    if errors:
        print("data errors: %s" % ", ".join(sorted(errors)))
    past_open = now.time() >= hhmm("09:45")

    if past_open and not index_bars and index not in errors and not state["positions"]:
        print("index has no bars today by 09:45: treating as a market holiday.")
        return 0
    if not bars or (past_open and not any(bars.values())):
        print("no data for any symbol this tick.")
        if not a.quiet:
            telegram("🚨 [PAPER] %s IST: no market data for any symbol this tick." % now.strftime("%H:%M"))
        return 1  # a failed run makes GitHub email you

    eng = Engine(cfg, state, notify=None if a.quiet else event_notifier)
    events = eng.step(now, bars, index_bars, kill_switch=kill_switch_on(), live=True)
    save_state(state)
    print("%s IST tick: %d symbols, %d open position(s), equity %.2f" % (
        now.strftime("%H:%M"), len(bars), len(state["positions"]), state["equity"]))
    for e in events:
        print("  %s %-8s %-10s %s" % (e["time"], e["kind"], e["symbol"], e["msg"]))
    return 0


def cmd_eod(a, cfg) -> int:
    state = load_state(cfg)
    now = parse_now(a.now) if a.now else now_ist()
    if not a.quiet:
        commands.process(state, cfg, kill_switch_on())
    if is_trading_day(now.date(), cfg["holidays"]) and state.get("date") != now.date().isoformat():
        msg = "🚨 [PAPER] %s: no tick ran today, so nothing was traded. Check the paper-trade workflow." % now.date()
        print(msg)
        if not a.quiet:
            telegram(msg)
        return 0
    if not state.get("date"):
        print("no state yet.")
        return 0
    d = state["date"]
    md = daily_markdown(state, cfg)
    path = os.path.join(ROOT, "reports", "daily", d + ".md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    repeat = False  # the backup schedule can run end-of-day a second time: don't post it twice
    if os.path.exists(path):
        with open(path) as fh:
            repeat = fh.read() == md
    with open(path, "w") as fh:
        fh.write(md)
    n = append_journal(os.path.join(ROOT, "journal", "trades.csv"), d, state["today"]["trades"])
    print(md)
    print("wrote %s, %d new journal row(s)" % (os.path.relpath(path, ROOT), n))
    if not a.quiet and not repeat:
        t = state["today"]
        telegram("📊 [PAPER] %s: net ₹%+.2f on %d trade(s), equity ₹%.2f, %d/%d ticks ran" % (
            d, t["realised"], len(t["trades"]), state["equity"], t.get("ticks", 0), expected_ticks(cfg)))
    return 0


def cmd_telegram_test(a, cfg) -> int:
    ok, why = send("✅ nse-algo-trader is connected to this chat.")
    print("telegram: %s" % why)
    return 0 if ok else 1


CACHE = os.path.join(ROOT, "data", "cache", "history.json")


def get_history(cfg: dict, range_: str, refresh: bool) -> dict:
    symbols = cfg["universe"] + [cfg["regime"]["index"]]
    if not refresh and os.path.exists(CACHE):
        hist = load_history(CACHE)
        if all(s in hist for s in symbols):
            print("using cached history (%s); --refresh to refetch" % os.path.relpath(CACHE, ROOT))
            return hist
    print("fetching %s of 5-minute bars for %d symbols + index..." % (range_, len(cfg["universe"])))
    hist = YahooSource().history(symbols, range_)
    save_history(CACHE, hist)
    return hist


def cmd_experiments(a, cfg) -> int:
    hist = get_history(cfg, a.range, a.refresh)
    rows = ex.run_all(cfg, hist, ex.load_variants(os.path.join(ROOT, "experiments.json")),
                      exclude_date=now_ist().date())
    md = ex.to_markdown(rows, rows[0]["report"])
    print(md)
    path = os.path.join(ROOT, "reports", "experiments-latest.md")
    with open(path, "w") as fh:
        fh.write(md)
    print("wrote %s" % os.path.relpath(path, ROOT))
    return 0


def cmd_backtest(a, cfg) -> int:
    index = cfg["regime"]["index"]
    hist = get_history(cfg, a.range, a.refresh)
    res = bt.run(cfg, hist, index, exclude_date=now_ist().date())
    rep = bt.split_report(res)
    md = bt.to_markdown(rep, cfg)
    print(md)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as fh:
            fh.write(md)
        with open(os.path.splitext(a.out)[0] + ".json", "w") as fh:
            json.dump({"report": rep, "trades": res["trades"], "daily": res["daily"]}, fh, indent=1)
        print("wrote %s" % a.out)
    return 0


def _write(name: str, md: str) -> None:
    print(md)
    path = os.path.join(ROOT, "reports", name)
    with open(path, "w") as fh:
        fh.write(md)
    print("wrote %s" % os.path.relpath(path, ROOT))


def cmd_signals(a, cfg) -> int:
    hist = get_history(cfg, a.range, a.refresh)
    name = "signals-latest.md"
    if a.strategies:
        cfg = ex.deep_merge(cfg, {"strategies": a.strategies.split(",")})
        name = "signals-%s.md" % a.strategies.replace(",", "-")
    if a.no_regime:
        cfg = ex.deep_merge(cfg, {"regime": {"require_green_day": False}})
    _write(name, research.study_markdown(research.signal_study(cfg, hist, now_ist().date())))
    return 0


def cmd_walkforward(a, cfg) -> int:
    hist = get_history(cfg, a.range, a.refresh)
    variants = ex.load_variants(os.path.join(ROOT, "experiments.json"))
    _write("walkforward-latest.md", research.walk_markdown(research.walk_forward(cfg, hist, variants, now_ist().date())))
    return 0


def cmd_commands(a, cfg) -> int:
    print("answered %d command(s)" % commands.process(load_state(cfg), cfg, kill_switch_on()))
    return 0


def cmd_status(a, cfg) -> int:
    state = load_state(cfg)
    print(json.dumps({k: state[k] for k in ("date", "equity", "positions")}, indent=1))
    t = state["today"]
    print("today: %d trade(s), net %.2f, %d event(s)" % (len(t["trades"]), t["realised"], len(t["events"])))
    print("kill switch: %s" % ("ON" if kill_switch_on() else "off"))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="algo")
    p.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    p.add_argument("--quiet", action="store_true", help="no Telegram messages")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tick", help="one paper-trading step (run every 5 minutes in market hours)")
    t.add_argument("--now", help="pin the clock, IST: '2026-10-29 10:15'")
    d = sub.add_parser("eod", help="end-of-day report + journal")
    d.add_argument("--now", help="pin the clock, IST: '2026-10-29 15:45'")
    b = sub.add_parser("backtest", help="replay history through the engine, net of costs")
    b.add_argument("--range", default="60d")
    b.add_argument("--out", default=os.path.join(ROOT, "reports", "backtest-latest.md"))
    b.add_argument("--refresh", action="store_true", help="refetch instead of using data/cache")
    e = sub.add_parser("experiments", help="run every variant in experiments.json on the same data")
    e.add_argument("--range", default="60d")
    e.add_argument("--refresh", action="store_true")
    for name, text in (("signals", "study every signal, without portfolio limits"),
                       ("walkforward", "pick variants on past data, score them on unseen data")):
        r = sub.add_parser(name, help=text)
        r.add_argument("--range", default="60d")
        r.add_argument("--refresh", action="store_true")
        if name == "signals":
            r.add_argument("--strategies", help="comma-separated, instead of config.json's")
            r.add_argument("--no-regime", action="store_true", help="drop the Nifty green-day filter")
    sub.add_parser("commands", help="answer waiting Telegram commands now")
    sub.add_parser("status")
    sub.add_parser("telegram-test", help="send one test message and print why it failed, if it did")
    a = p.parse_args(argv)
    cfg = load_cfg(a.config)
    return {"tick": cmd_tick, "eod": cmd_eod, "backtest": cmd_backtest, "experiments": cmd_experiments,
            "status": cmd_status, "telegram-test": cmd_telegram_test, "signals": cmd_signals,
            "walkforward": cmd_walkforward, "commands": cmd_commands}[a.cmd](a, cfg)


if __name__ == "__main__":
    sys.exit(main())
