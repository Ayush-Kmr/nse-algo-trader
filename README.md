# nse-algo-trader

Automated **paper** trading for NSE intraday cash equity, running unattended on GitHub Actions.
Every rupee figure is **net of Angel One charges and slippage**. No real orders exist in this repo.

## What runs, and when (IST, Mon–Fri)

| when | workflow | what |
|---|---|---|
| every 5 min, 09:30–15:25 | `paper-trade` | fetch completed 5-min bars, manage open positions, look for entries, risk-check, paper-fill |
| 15:15 | (inside `paper-trade`) | hard square-off of anything still open |
| 15:45 | `end-of-day` | daily report → `reports/daily/`, trades → `journal/trades.csv`, state committed |
| Sat 10:00 | `backtest` | replay the last 60 days through the same engine → `reports/backtest-latest.md` |
| every push | `tests` | offline unit tests |

Your laptop can be off. A failed run (e.g. no data at all) turns red and GitHub emails you.

## How a trade happens

```
Yahoo 5-min bars ─► strategy (orb, vwap_reclaim) ─► signal ─► RISK ENGINE ─► paper broker ─► journal
 completed bars      long only, one per symbol/day             pure, no network   stop/target/square-off
 only                                                          BLOCK is final     every fill charged
```

**Risk engine** (`algo/risk.py`) blocks an entry if any of these fail:
kill switch · entry window 09:30–14:45 · symbol already traded today · max 2 open positions ·
max 4 trades/day · daily loss limit 1% (losses so far + open risk + this trade) · stop below entry ·
size ≥ 1 after costs · no leverage (cash) · position ≤ 60% of equity ·
**net reward:risk ≥ 1.5 after charges** · charges ≤ 25% of the risk budget.
Exits never pass through it: getting out is never blocked.

**Sizing** (`algo/sizing.py`): largest quantity whose loss at the stop — slippage and *all* charges
included — fits 0.5% of equity.

**Costs** (`algo/costs.py`): brokerage (₹20 or 0.1%, lower), STT 0.025% sell, exchange 0.00297%,
SEBI ₹10/crore, stamp 0.003% buy, GST 18%. Rates in `config.json` → `costs`, marked
`verified: false` until checked against Angel One's live charge sheet.

**Paper fills** are conservative: stop and target in the same bar → the stop wins; a gap through the
stop fills at the open; square-off is a marketable limit, not a market order.

**Regime filter**: no new longs while the Nifty 50 index is below its day's open. Missing index data → no entries.

## Controls

- **Kill switch** — GitHub → Settings → Secrets and variables → Actions → *Variables* →
  `KILL_SWITCH` = `1`. Stops new entries from the next run; open positions are still managed and squared
  off. Works from the GitHub mobile app. Delete it or set `0` to resume.
- **Telegram alerts** (optional) — add secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
  You get every entry, exit, critical event and the end-of-day summary.
- **Run now** — Actions → pick a workflow → *Run workflow*.
- **Settings** — `config.json` (capital, risk %, limits, universe, strategy parameters).

## Local use

```bash
python3 -m unittest discover -s tests -t .       # offline tests
python3 -m algo backtest                           # 60 days, net of costs
python3 -m algo tick --now "2026-10-29 10:15"      # one step at a pinned time
python3 -m algo status
python3 -m algo eod
```

Python 3.9+, standard library only. Nothing to install.

## Current honest status

See `reports/backtest-latest.md`. The first run (2026-10-29, 59 sessions, 25 Nifty names) **lost money
net of costs**, and charges were about twice the gross loss. That is the point of the backtest gate:
no strategy here has shown an edge yet. Change one idea at a time and re-run; do not tune parameters
until the backtest looks good — that only fits the past.

## Why this cannot place real orders (yet)

All SmartAPI orders count as algo orders under NSE's retail-algo rules: they must come from a
**static IP registered with Angel One**, be tagged, and use LIMIT / SL-L only. GitHub's runners have
changing IPs, so live trading needs a VPS. The gates before `algo/broker/angelone.py` is written:

1. Positive **net** out-of-sample expectancy over 30+ trades in the backtest
2. 30+ sessions of forward paper trading here, agreeing with the backtest
3. Static-IP VPS, Angel One compliance confirmed, broker-resident stops + a separate supervisor
4. Your explicit go-ahead, then minimum size

Design and audit: `docs/UNATTENDED_DESIGN.md`, `docs/PHASE1_AUDIT.md`.

## Limits of the data

Yahoo Finance's chart endpoint is free, unofficial and can lag or rate-limit, especially from cloud
IPs. GitHub may start scheduled runs several minutes late; signals older than 2 bars are expired
rather than chased. NSE holidays are detected from missing index data; add known ones to
`config.json` → `holidays`.

Not financial advice. Most intraday traders lose money net of costs.
