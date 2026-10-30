# nse-algo-trader

Automated **paper** trading for NSE intraday cash equity, running unattended on GitHub Actions.
Every rupee figure is **net of Angel One charges and slippage**. No real orders exist in this repo.

## What runs, and when (IST, Mon–Fri)

| when | workflow | what |
|---|---|---|
| every 5 min, 09:32–15:27 | `paper-trade` | fetch completed 5-min bars, manage open positions, look for entries, risk-check, paper-fill |
| 15:15 | (inside `paper-trade`) | hard square-off of anything still open |
| 15:45 | `end-of-day` | daily report → `reports/daily/`, trades → `journal/trades.csv`, state committed |
| Sat 10:00 | `backtest` | backtest, signal study and walk-forward on the last 60 days → `reports/` |
| every push | `tests` | offline unit tests |

Your laptop can be off. A failed run (e.g. no data at all) turns red and GitHub emails you.

**The clock is cron-job.org, not GitHub.** GitHub's scheduler ran 1 of 72 ticks on its first day and
skipped end-of-day. cron-job.org now triggers the runs on IST time, and it emails you after 2 failed
calls. GitHub's cron remains as a sparse backup: hourly ticks from 10:17 and end-of-day at 16:15.

Telegram is the final check: **no "engine live" message by about 09:45 on a trading day means ticks
are not running.** A gap of 20+ minutes also alerts, and the end-of-day message shows how many of
the 72 ticks ran.

## Schedule setup

1. Sign up at [cron-job.org](https://cron-job.org), then create an API key under Settings.
2. On GitHub, create a [fine-grained token](https://github.com/settings/personal-access-tokens/new):
   repository access *only this repo*, permission **Actions: Read and write**, nothing else. Pick an
   expiry and note it: when it lapses, calls fail and cron-job.org emails you.
3. Run `python3 scripts/setup_cronjob.py` and paste both when prompted. It creates 4 jobs and is safe
   to rerun. The GitHub token is stored in those jobs at cron-job.org.

To pause everything, disable the jobs in the cron-job.org console. Use `KILL_SWITCH` to stop entries
but keep managing positions. The schedule costs about 80 Actions minutes a trading day, roughly
1,700 a month, so check your plan's allowance: a private repo on the free plan gets 2,000.

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
**net reward:risk ≥ 1.5 after charges** · charges ≤ 25% of this trade's risk budget ·
position ≥ ₹5,000.
Exits never pass through it: getting out is never blocked.

**Sizing** (`algo/sizing.py`): largest quantity whose loss at the stop — slippage and *all* charges
included — fits 0.5% of equity.

**Costs** (`algo/costs.py`): brokerage (₹20 or 0.1%, lower, ₹5 minimum), STT 0.025% sell, exchange
0.0030699%, SEBI ₹10/crore, stamp 0.003% buy, GST 18%. Rates in `config.json` → `costs`, taken from
Angel One's charges page and marked `verified: false` until matched to a real contract note.

**Paper fills** are conservative: stop and target in the same bar → the stop wins; a gap through the
stop fills at the open; square-off is a marketable limit, not a market order. Every fill pays 0.05%
slippage plus 0.01% half spread (both assumptions). If a tick runs late,
the entry uses the latest close, and a signal that has moved more than 0.3% is dropped, not chased.

**Regime filter**: no new longs while the Nifty 50 index is below its day's open. Missing index data → no entries.

## Controls

- **Kill switch** — GitHub → Settings → Secrets and variables → Actions → *Variables* →
  `KILL_SWITCH` = `1`. Stops new entries from the next run; open positions are still managed and squared
  off. Works from the GitHub mobile app. Delete it or set `0` to resume.
- **Telegram channel** — see below. You get the morning "engine live", every entry and exit,
  warnings, schedule gaps, the kill switch and the end-of-day summary.
- **Run now** — Actions → pick a workflow → *Run workflow*.
- **Settings** — `config.json` (capital, risk %, limits, universe, strategy parameters).

## Telegram channel setup

1. In Telegram, message **@BotFather**, send `/newbot`, and copy the token. Treat it like a password.
2. Create a channel, then add your bot as an **admin** with *Post Messages* permission.
3. Find the chat id. A public channel can use `@channelname`. For a private channel, post a message
   there and forward it to **@userinfobot**, or read `chat.id` (it starts with `-100`) from
   `https://api.telegram.org/bot<token>/getUpdates`.
4. Add both as repo secrets. Each command prompts for the value, so it never lands in shell history:
   ```bash
   gh secret set TELEGRAM_BOT_TOKEN -R Ayush-Kmr/nse-algo-trader
   gh secret set TELEGRAM_CHAT_ID -R Ayush-Kmr/nse-algo-trader
   ```
5. Test it: `gh workflow run telegram-test.yml -R Ayush-Kmr/nse-algo-trader`. A failed run shows
   Telegram's reason, such as `chat not found` (wrong id) or `Forbidden` (bot is not an admin).

## Telegram commands

Post these in the channel: `/status`, `/positions`, `/trades`, `/pnl`, `/schedule`, `/help`. They
are read-only and only your channel is answered. Replies arrive at the next tick, so up to 5 minutes
in market hours. Outside market hours they depend on two best-effort runs a day, which can be hours
late or skipped.

## Local use

```bash
python3 -m unittest discover -s tests -t .       # offline tests
python3 -m algo backtest                           # 60 days, net of costs
python3 -m algo experiments                        # every variant in experiments.json, same data
python3 -m algo signals                            # every signal, without portfolio limits
python3 -m algo walkforward                        # pick on the past, score on unseen days
python3 -m algo learn                              # train a filter on past days, score on unseen ones
python3 -m algo stability                          # stress the live path with injected faults
python3 -m algo weekly                             # refit, read paper trades, post the report
python3 -m algo commands                           # answer waiting Telegram commands now
python3 -m algo tick --now "2026-10-29 10:15"      # one step at a pinned time
python3 -m algo status
python3 -m algo eod
```

Python 3.9+, standard library only. Nothing to install.

## Current honest status

See `reports/backtest-latest.md`. The first run (2026-10-29, 59 sessions, 25 Nifty names) **lost money
net of costs**, and charges were about twice the gross loss. That is the point of the backtest gate:
no strategy here has shown an edge yet. A second round tested 12 pre-registered variants (exits,
filters, ranges): all lost in-sample. A signal study of 472 signals then showed the entries lose even
before charges (−0.20R), and walk-forward lost on unseen days. Details: `docs/RESEARCH_LOG.md`.

## Why this cannot place real orders (yet)

All SmartAPI orders count as algo orders under NSE's retail-algo rules: they must come from a
**static IP registered with Angel One**, be tagged, and use LIMIT / SL-L only. GitHub's runners have
changing IPs, so live trading needs a VPS. The gates before `algo/broker/angelone.py` is written:

1. **Net** out-of-sample avg R over 30+ trades with its 95% lower bound above zero, corrected for
   the number of variants tried
2. 30+ sessions of forward paper trading here, agreeing with the backtest
3. Static-IP VPS, Angel One compliance confirmed, broker-resident stops + a separate supervisor
4. Your explicit go-ahead, then minimum size

Architecture: `docs/ARCHITECTURE.md`. Design and audit: `docs/UNATTENDED_DESIGN.md`, `docs/PHASE1_AUDIT.md`.

## Limits of the data

Yahoo Finance's chart endpoint is free, unofficial and can lag or rate-limit, especially from cloud
IPs. Runs can still start a minute or two late; signals older than 2 bars are expired
rather than chased. NSE holidays are detected from missing index data; add known ones to
`config.json` → `holidays`.

Not financial advice. Most intraday traders lose money net of costs.
