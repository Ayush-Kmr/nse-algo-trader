# Architecture

What the system is, what it can do today, and what stands between it and real orders.
For the reasoning behind the safety design, see `UNATTENDED_DESIGN.md`.

## In one paragraph

A paper-trading engine for NSE intraday cash equity. It wakes every 5 minutes in market hours, reads
5-minute bars, manages open paper positions, looks for long entries, puts each through a risk
engine, and simulates fills net of Angel One charges. It runs on GitHub Actions, so a laptop is not
needed. **It cannot place a real order:** the only broker is simulated.

## Runtime

```
 cron-job.org (IST clock)         GitHub cron (sparse backup)
   09:32-15:27 every 5 min          hourly 10:17-15:17, 16:15
   15:45 end of day                 16:50 and 20:50 for commands
        │  workflow_dispatch               │
        └──────────────┬───────────────────┘
                       ▼
 ┌─ GitHub Actions job (one at a time, group trading-state) ──────────────┐
 │  restore state (Actions cache, else copy committed by end-of-day)      │
 │                                                                        │
 │  1. Telegram commands ──► read-only replies, marked read               │
 │  2. Trading day and market hours?  No: stop here                       │
 │  3. Yahoo bars, completed bars only                                    │
 │  4. Engine.step                                                        │
 │       heartbeat ─ count tick, "engine live", gap alert                 │
 │       exits first ─ stop, target, trailing stop, 15:15 square-off      │
 │       stale data, kill switch, entry window, Nifty regime              │
 │       strategies ─ signal ─ reprice if late ─ rank by relative strength│
 │       RISK ENGINE ─ pure, BLOCK is final                               │
 │       PaperBroker ─ simulated fill, every round trip charged           │
 │                                                                        │
 │  save state to the Actions cache                                       │
 └───────────────┬────────────────────────────────────────────────────────┘
                 ▼
 Telegram channel: engine live, entries, exits, warnings, gaps, summary
 Repo (end of day): reports/daily/, journal/trades.csv, state/state.json
```

Saturday `backtest` refreshes the backtest, signal study and walk-forward reports. Every push runs
the offline tests.

## Modules

| Module | Job |
|---|---|
| `algo/__main__.py` | Command line; connects data, engine, reports and alerts |
| `algo/engine.py` | The trading loop, shared by paper ticks and the backtest |
| `algo/strategies/` | `orb`, `vwap_reclaim`: completed bars in, at most one long signal out |
| `algo/risk.py` | Entry checks. No network and no clock of its own. Exits never pass through it |
| `algo/sizing.py` | Largest quantity whose loss at the stop, costs included, fits the budget |
| `algo/costs.py` | Angel One charges on every round trip |
| `algo/broker/base.py` | The `Broker` interface the engine uses |
| `algo/broker/paper.py` | Simulated fills |
| `algo/broker/angelone.py` | Stub that raises. Live trading is not built |
| `algo/data.py` | Yahoo bars, completed-bar rule, history cache |
| `algo/notify.py` | Posts to the Telegram channel |
| `algo/commands.py` | Read-only slash commands |
| `algo/report.py` | Daily report and permanent trade journal |
| `algo/backtest.py` | Replays history through the engine; applies the gate |
| `algo/experiments.py` | Compares pre-registered variants on the same data |
| `algo/research.py` | Signal study and walk-forward |
| `algo/learn.py` | Walk-forward learned signal filter (research only) |
| `algo/stability.py` | Stress test of the live path |
| `algo/chart.py` | Chart images and plain-words alert captions |
| `algo/demo.py` | Labelled demo and made-up test days for the channel |
| `scripts/setup_cronjob.py` | Creates the cron-job.org jobs |

## What it can do today

**Trading (paper):** opening-range breakout and VWAP reclaim, long only, on 25 Nifty stocks, with
fixed targets and optional breakeven or trailing stops, flat by 15:15.

**Risk:** 0.5% of equity per trade, 1% daily loss limit, 2 open positions, 4 trades a day, one trade
per symbol per day, no leverage, 60% position cap, ₹5,000 minimum position, 1.5 minimum net
reward:risk, charges at most 25% of the trade's risk, and a kill switch.

**Fill realism:** charges including the ₹5 minimum brokerage, 0.05% slippage, 0.01% half spread, stop
beats target within a bar, gaps fill at the open, late ticks reprice and do not chase.

**Monitoring:** morning heartbeat, 20-minute gap alert, stale-data block, unmanaged-position alert,
no-tick-today alert, tick count, and failure emails from cron-job.org and GitHub.

**Research:** portfolio backtest, 12 pre-registered variants, signal study, walk-forward, and a gate
that needs 30+ out-of-sample trades with a lower bound on average R above zero.

## Telegram commands

Post these in the channel. They are read-only, and only that channel is answered.

| Command | Reply |
|---|---|
| `/status` | Equity, today's P&L, open positions, kill switch |
| `/positions` | Open positions with stop and target |
| `/trades` | Today's closed trades |
| `/pnl` | Total P&L and the last 5 days |
| `/schedule` | Ticks that ran today |
| `/help` | The command list |

Nothing listens between runs, so replies arrive at the next tick: up to 5 minutes in market hours.
Outside them the only runs are two best-effort GitHub schedules a day, which can be hours late or
skipped. Telegram drops unread commands after 24 hours. Channels do not show a command menu, so type
the command.

## Limits to know about

- **Paper is not execution.** Fills are modelled from bars. Real queueing, partial fills and rejected
  orders do not exist here, and a late tick still fills at a past bar's close.
- **Yahoo is an unofficial, free source** and can lag or block cloud IPs.
- **Single points of failure:** cron-job.org and GitHub Actions. If either stops, only alerts or
  missing messages show it.
- **Sample:** 60 sessions from one market period, and today's Nifty names (survivorship bias).
- **Tick size** is 0.05 for all stocks. This matters only for live orders; check it first.
- **Charges** are from Angel One's page and unconfirmed against a contract note.

## Stability

`python3 -m algo stability` replays the history through the tick path, reloading state from JSON on
every tick, then again with lost ticks, symbols and index data. Clean replays must match the backtest
trade for trade, and no chaos replay may break a limit. It runs every Saturday. A corrupted state
file restarts the paper account with an alert, a crash posts to the channel, and a failed chart still
sends the text.

## What is deliberately not built

These are needed for real orders. They wait on the gate in `README.md`, which nothing has passed:

| Needed for live | Status |
|---|---|
| Strategy with a proven net edge | **None. This is the blocker** |
| Static-IP VPS registered with Angel One | Not started |
| SmartAPI adapter: LIMIT and SL-L only, order tagging | Stub |
| Asynchronous orders, partial fills, idempotency | Not built; the `Broker` interface assumes instant fills |
| Broker-resident stop placed on every fill | Not built |
| Separate supervisor, heartbeat, dead-man switch | Not built |
| Reconcile with the broker before trading | Not built |
| Limit-order square-off ladder | Not built |
| SmartAPI data in place of Yahoo | Not built |

Paper protection lives inside the process, which is acceptable only because no money is at risk.
