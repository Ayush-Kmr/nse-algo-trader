"""python -m algo tick | eod | backtest | experiments | signals | walkforward | learn | stability | weekly | survey | delivery | pit | ingest | lab | live | extra | status | commands | telegram-test"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import date, timedelta
import os
import sys
import time

from . import backtest as bt
from . import bhav
from . import commands
from . import delivery
from . import demo
from . import experiments as ex
from . import extra
from . import lab
from . import learn
from . import feeds
from . import store
from . import longtest
from . import playbook
from . import research
from . import stability
from . import survey
from . import weekly
from . import data
from .data import YahooSource, load_history, save_history
from .engine import Engine, new_state
from .chart import chart_notifier
from .notify import send, telegram
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
    if not os.path.exists(STATE):
        return new_state(cfg)
    try:
        with open(STATE) as fh:
            state = json.load(fh)
        fresh = new_state(cfg)
        for key, value in fresh.items():
            state.setdefault(key, value)
        for key, value in fresh["today"].items():
            state["today"].setdefault(key, value)
        return state
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        msg = "🚨 [PAPER] the saved state could not be read (%s), so the paper account restarted." % type(e).__name__
        print(msg)
        telegram(msg)
        os.replace(STATE, STATE + ".corrupt")
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

    eng = Engine(cfg, state, notify=None if a.quiet else chart_notifier(bars))
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


def cmd_learn(a, cfg) -> int:
    hist = get_history(cfg, a.range, a.refresh)
    _write("learn-latest.md", learn.to_markdown(learn.run(cfg, hist, now_ist().date())))
    return 0


def cmd_telegram_demo(a, cfg) -> int:
    sent = demo.run()
    print("demo: sent %d of %d" % (sent, len(demo.MESSAGES)))
    return 0 if sent == len(demo.MESSAGES) else 1


def cmd_telegram_sim(a, cfg) -> int:
    start = time.time()
    events = demo.simulate(cfg, now_ist().date())
    print("sim: %d events in %.1fs" % (len(events), time.time() - start))
    for e in events:
        print("  %s %-8s %s" % (e["time"], e["kind"], e["msg"]))
    return 0


def cmd_stability(a, cfg) -> int:
    hist = get_history(cfg, a.range, a.refresh)
    rep = stability.run(cfg, hist, now_ist().date())
    _write("stability-latest.md", stability.to_markdown(rep))
    return 0 if stability.passed(rep) else 1


def cmd_weekly(a, cfg) -> int:
    hist = get_history(cfg, a.range, a.refresh)
    with open(os.path.join(ROOT, "universe_200.txt")) as fh:
        universe = fh.read().split()
    short, long_rep, paper = weekly.run(cfg, hist, universe, os.path.join(ROOT, "journal", "trades.csv"), now_ist().date())
    _write("learn-latest.md", learn.to_markdown(short))
    _write("longtest-latest.md", longtest.to_markdown(long_rep))
    msg = weekly.message(short, long_rep, paper)
    print(msg)
    if not a.quiet:
        telegram(msg)
    return 0


def cmd_survey(a, cfg) -> int:
    with open(os.path.join(ROOT, "universe_200.txt")) as fh:
        universe = fh.read().split()
    hist = longtest.fetch(universe + [cfg["regime"]["index"]])
    print("fetched %d symbols" % len(hist))
    _write("survey-latest.md", survey.to_markdown(survey.run(cfg, hist, now_ist().date())))
    return 0


def cmd_delivery(a, cfg) -> int:
    with open(os.path.join(ROOT, "universe_500.txt")) as fh:
        wide = fh.read().split()
    with open(os.path.join(ROOT, "universe_200.txt")) as fh:
        today = set(fh.read().split())
    closes, traded = delivery.fetch(wide + [delivery.ETF, delivery.INDEX])
    print("fetched %d symbols" % len(closes))
    fixed = {s: c for s, c in closes.items() if s in today or s in (delivery.ETF, delivery.INDEX)}
    _write("delivery-latest.md", delivery.to_markdown(delivery.run(closes, traded)) + "\n" +
           delivery.to_markdown(delivery.run(fixed)))
    return 0


def cmd_extra(a, cfg) -> int:
    with open(os.path.join(ROOT, "universe_200.txt")) as fh:
        universe = fh.read().split()
    index = cfg["regime"]["index"]
    today = now_ist().date()
    five = YahooSource(pause=0.05).history(universe + [index], "60d")
    hourly = longtest.fetch(universe + [index])
    industry = extra.load_industries(os.path.join(ROOT, "universe_200.csv"))
    _write("extra-latest.md", extra.to_markdown({
        "Finer timing, 5-minute bars": extra.finer(cfg, five, today),
        "Groww guide rules, 5-minute bars": extra.guide(cfg, five, today),
        "News proxy: big gaps on heavy volume": extra.news_proxy(cfg, hourly, today),
        "Pairs trading": extra.pairs(cfg, hourly, industry, today)}))
    return 0


def cmd_pit(a, cfg) -> int:
    root = os.path.join(ROOT, "data", "bhav")
    print(bhav.download(root, date(2008, 1, 1), now_ist().date() - timedelta(days=1)))
    moves, traded = bhav.load(root)
    index = {b.ts.date(): b.close for b in data.fetch_bars(delivery.INDEX, "20y", "1d", retries=2, timeout=30)}
    closes = bhav.adjusted(moves)
    closes[delivery.INDEX] = index
    p = delivery.Prices(closes)
    names = bhav.stocks_only(s for s in closes if s not in (delivery.ETF, delivery.INDEX))
    ever = sorted({s for m in delivery.by_turnover(p, traded, names).values() for s in m})
    yahoo, _ = delivery.fetch(ever + [delivery.ETF])
    print("%d symbols, %d ever in the top 200, %d on Yahoo" % (len(closes), len(ever), len(yahoo)))
    closes = bhav.adjusted(moves, yahoo)
    closes[delivery.INDEX] = index
    rep = delivery.run(closes, traded)
    gone = sum(1 for s, c in closes.items() if s != delivery.INDEX and max(c) < now_ist().date() - timedelta(days=30))
    _write("pit-latest.md", "%d of the %d symbols stopped trading before the end, and they are included.\n\n" % (
        gone, len(closes)) + delivery.to_markdown(rep, "Delisted stocks are included, but only stocks Yahoo still lists have exact split "
        "adjustment. The rest use clean-ratio matching, so a bonus or demerger can look like a crash. That most affects strategies "
        "buying big fallers: treat the 1-month losers row as unreliable. Tax is not included."))
    return 0


def _universe(path: str = "universe_200.txt") -> list:
    with open(os.path.join(ROOT, path)) as fh:
        return fh.read().split()


def cmd_ingest(a, cfg) -> int:
    """Download, validate and store broker bars. Stops if the token is missing: nothing is invented."""
    end = now_ist().date() - timedelta(days=1)
    start = end - timedelta(days=a.days)
    universe = _universe()
    root = os.path.join(ROOT, "data", "market")
    if a.source == "dhan":
        src, ids = feeds.DhanSource(), feeds.dhan_security_ids(universe)
    else:
        src = feeds.UpstoxSource()
        ids = {r["Symbol"].strip(): r["ISIN Code"].strip() for r in csv.DictReader(open(os.path.join(ROOT, "universe_200.csv")))}
    bad = 0
    for sym in universe:
        if sym not in ids:
            print("no instrument id for %s, skipped" % sym)
            continue
        bars = src.history(ids[sym], start, end, a.minutes)
        rep = store.validate(sym, bars, a.minutes)
        store.save(root, src.name, sym, store.clean(bars, rep), a.minutes, rep)
        bad += len(rep["bad"])
    print("stored in data/market/%s, %d bad bar(s) excluded" % (src.name, bad))
    return 0


def cmd_lab(a, cfg) -> int:
    index = cfg["regime"]["index"]
    today = now_ist().date()
    if a.source == "yahoo":
        hist = YahooSource(pause=0.05).history(_universe() + [index], "60d")
    else:
        folder = os.path.join(ROOT, "data", "market", a.source, "%dm" % a.minutes)
        hist = {f[:-4].replace("_", "^", 1) if f.startswith("_") else f[:-4]: store.load(os.path.join(folder, f), a.minutes)
                for f in os.listdir(folder) if f.endswith(".csv")}
    reports = {s: store.validate(s, b, a.minutes) for s, b in hist.items()}
    hist = {s: store.clean(b, reports[s]) for s, b in hist.items()}
    print("%d symbols, %d bad bars excluded, %d gaps left as gaps" % (
        len(hist), sum(len(r["bad"]) for r in reports.values()), sum(len(r["gaps"]) for r in reports.values())))
    _write("lab-latest.md", lab.to_markdown(lab.run(cfg, hist, today), a.source))
    return 0


def cmd_playbook(a, cfg) -> int:
    index = cfg["regime"]["index"]
    today = now_ist().date()
    names = _universe()
    history = YahooSource(pause=0.05).history(names + [index], "60d")
    history = {s: [b for b in bars if b.ts.date() < today] for s, bars in history.items()}
    daily = {}
    for s in names:
        try:
            bars = data.fetch_bars(s, "20y", "1d", retries=2, timeout=30)
        except Exception as e:  # noqa: BLE001 - a missing stock narrows the test, it does not stop it
            print("  skip %s: %s" % (s, type(e).__name__))
            continue
        daily[s] = [b for b in bars if b.ts.date() < today]
    _write("playbook-latest.md", playbook.to_markdown(playbook.run(cfg, history, daily)))
    return 0


def cmd_live(a, cfg) -> int:
    """Paper trading from the Dhan WebSocket. Needs an always-on machine, tokens and requirements-live.txt."""
    from . import live
    feeds._require("DHAN_ACCESS_TOKEN")
    feeds._require("DHAN_CLIENT_ID")
    ids = feeds.dhan_security_ids(cfg["universe"])
    missing = sorted(set(cfg["universe"]) - set(ids))
    if missing:
        print("no Dhan id for: %s" % ", ".join(missing))
    all_ids = dict(ids, **{cfg["regime"]["index"]: feeds.NIFTY_50_ID})
    engine = live.PaperLive(cfg, load_state(cfg), all_ids, live.state_saver(STATE), os.path.join(ROOT, "state", "KILL"))

    async def watch():
        task = asyncio.create_task(live.run_dhan(engine, list(ids.values()), (feeds.NIFTY_50_ID,)))
        while True:
            await asyncio.sleep(5)
            engine.check_stale(now_ist())
            if task.done():
                return task.result()

    asyncio.run(watch())
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
                       ("walkforward", "pick variants on past data, score them on unseen data"),
                       ("learn", "train a signal filter on past days, score it on unseen days"),
                       ("stability", "stress the live path with injected faults"),
                       ("weekly", "refit on the newest data and post the learning report")):
        r = sub.add_parser(name, help=text)
        r.add_argument("--range", default="60d")
        r.add_argument("--refresh", action="store_true")
        if name == "signals":
            r.add_argument("--strategies", help="comma-separated, instead of config.json's")
            r.add_argument("--no-regime", action="store_true", help="drop the Nifty green-day filter")
    sub.add_parser("telegram-demo", help="post a labelled walk-through of the channel's messages")
    sub.add_parser("telegram-sim", help="replay made-up days through the real engine, alerts on")
    sub.add_parser("pit", help="delivery test on NSE bhavcopies, including delisted stocks")
    g = sub.add_parser("ingest", help="download and validate broker bars (needs a token)")
    g.add_argument("source", choices=["dhan", "upstox"])
    g.add_argument("--minutes", type=int, default=5, choices=[1, 5])
    g.add_argument("--days", type=int, default=365)
    n = sub.add_parser("lab", help="four strategy families with train, validation and test splits")
    n.add_argument("--source", default="yahoo", choices=["yahoo", "dhan", "upstox"])
    n.add_argument("--minutes", type=int, default=5, choices=[1, 5])
    sub.add_parser("playbook", help="day-trader-skill's rules on NSE stocks, with Indian charges")
    sub.add_parser("live", help="paper trade from the Dhan WebSocket on an always-on machine")
    sub.add_parser("delivery", help="multi-month delivery strategies with real charges")
    sub.add_parser("extra", help="finer timing, news proxy and pairs tests")
    sub.add_parser("survey", help="contest of the main intraday strategy families")
    sub.add_parser("commands", help="answer waiting Telegram commands now")
    sub.add_parser("status")
    sub.add_parser("telegram-test", help="send one test message and print why it failed, if it did")
    a = p.parse_args(argv)
    cfg = load_cfg(a.config)
    try:
        return _dispatch(a, cfg)
    except Exception as e:
        if a.cmd in ("tick", "eod") and not a.quiet:  # a crash must reach the channel, not only the log
            telegram("🚨 [PAPER] %s crashed: %s. Any open paper position is not being managed." % (a.cmd, type(e).__name__))
        raise


def _dispatch(a, cfg) -> int:
    return {"tick": cmd_tick, "eod": cmd_eod, "backtest": cmd_backtest, "experiments": cmd_experiments,
            "status": cmd_status, "telegram-test": cmd_telegram_test, "signals": cmd_signals,
            "walkforward": cmd_walkforward, "commands": cmd_commands, "learn": cmd_learn, "stability": cmd_stability, "weekly": cmd_weekly, "survey": cmd_survey, "delivery": cmd_delivery, "ingest": cmd_ingest, "lab": cmd_lab, "live": cmd_live, "pit": cmd_pit, "playbook": cmd_playbook, "extra": cmd_extra,
            "telegram-demo": cmd_telegram_demo, "telegram-sim": cmd_telegram_sim}[a.cmd](a, cfg)


if __name__ == "__main__":
    sys.exit(main())
