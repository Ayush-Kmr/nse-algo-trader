# Unattended Automation — Design Note

Date: 2026-10-29
Status: design only. Nothing built. AUTO_EXECUTION remains disabled per the project brief.

---

## 0. Regulatory question from PHASE1_AUDIT.md §8 — now RESOLVED

The NSE retail-algo FAQ (03-11-2025) states plainly:

> "all orders received via API from clients are considered Algo orders"

So the approval-required/automated distinction does **not** exempt you. Any order your code sends
through SmartAPI is an algo order. The consequences bind in both modes:

| Rule | Source |
|---|---|
| Static IP required, hosted at your end | "Tech Savvy client is required to host the Algo using a static IP at their end." |
| Market orders prohibited for algos | "Algo orders with order type as Market Order are not permitted." IOC also barred in Commodity. |
| Order tagging | First 12 digits fixed `444444444444`; 13th digit `0`, `2`, or `4`. Standardised tagging applies within the 10 OPS threshold. |
| Monthly mock trading | **Not** required for individual tech-savvy clients. |
| P&L responsibility | Yours. Broker retains RMS responsibility. |

**You are permitted to write and self-host your own automated algo as a "tech-savvy client".**
This is a recognised category, not a grey area. The conditions are the static IP, the tagging, the
order-type restriction, and staying under 10 OPS (you will run a handful of orders per *day*).

Primary circulars to read before going live: NSE/INVG/69255 (22-07-2025) and NSE/INVG/70309
(19-09-2025). These prevail over the FAQ. I am not a compliance advisor — confirm with Angel One.

---

## 1. "Runs when the laptop is off" — what that actually requires

A MacBook cannot host this. Not because of software, but because it sleeps, its IP is dynamic, and
its uptime is not yours to guarantee. The code must live on a machine that is always on and holds a
static IP you have registered with Angel One.

**Option A — VPS (recommended).** An India-region VPS with a dedicated static IPv4. 2 vCPU / 4 GB
is more than enough; this workload is tiny. Mumbai region minimises latency to NSE. Register that
IP in the SmartAPI dashboard under Add App. Remember: IP mapping can be changed **at most once per
calendar week**, so do not pick a provider that recycles addresses.

**Option B — static-IP egress proxy.** Keep compute anywhere, route broker traffic through a fixed
IP. More moving parts, one more failure point in the order path. Only worth it if you already have
infrastructure you want to keep.

**Option C — broker-hosted no-code platform.** No static IP needed, but you give up your own logic.
Not what you are building.

Register a **secondary static IP** as backup where the provider allows it.

---

## 2. The one principle that makes unattended trading survivable

> **A protective stop that lives inside your process is not a protective stop.**

When nobody is watching, the question is not "what does my code do when the trade goes wrong" but
"what happens to my open position when *my code* goes wrong". Process crash, OOM kill, kernel
panic, network partition, provider outage, expired session token, a bug in your own exception
handler. Every one of these leaves a live position with no supervision.

So protection is layered, and each layer survives the failure of the one above it:

**Layer 1 — Broker-resident exits (primary).**
The instant an entry fills, a stop-loss-limit order for the full filled quantity goes to the
exchange and *sits there*. It executes whether your VPS is alive or not. This is the only layer
that is genuinely independent of your infrastructure. Everything else is a backstop.

Open question that must be answered before live: does SmartAPI ROBO survive client disconnect, and
is it available for cash intraday? If the answer is no, the fallback is an independent SL-L order
placed immediately post-fill and reconciled continuously — still broker-resident, just managed as
two orders rather than a bracket.

**Layer 2 — Supervisor process (separate PID, separate session).**
A second, deliberately small program. It does not run strategies. It polls broker positions on an
interval, and if it finds a position with no live protective order against it, it places one and
alerts you. It is the thing that catches "the main app died between fill and stop placement" — the
single most dangerous window in the whole system. Keep it under a few hundred lines so it is
auditable and almost impossible to break.

**Layer 3 — Dead-man's switch.**
The main app writes a heartbeat every N seconds. The supervisor watches it. Missed heartbeats past
a threshold during market hours trigger: cancel all pending entry orders, verify protective orders
exist on every open position, flatten if configured, Telegram alert. A heartbeat that stops is
treated as a failure, never as "probably fine".

**Layer 4 — Time-based hard square-off.**
An unconditional flatten at a fixed time (e.g. 15:15 IST), owned by the supervisor, not the
strategy engine. It runs regardless of what any strategy thinks. Because market orders are banned
for algos, this is a marketable limit with a bounded re-price ladder — place at a price a few ticks
through the book, and if unfilled after a short interval, re-price and retry, with a cap on attempts
and an escalating alert if it still will not fill.

**Layer 5 — systemd.**
`Restart=always` with a backoff. On every boot the app *reconciles before it trades*: pull live
positions and orders from the broker, rebuild state from that, compare against the DB, and refuse
to take new entries until reconciliation is clean. Local state is never authoritative. A restart
mid-trade must not produce a duplicate order, which is what idempotency keys are for.

---

## 3. Risk and P&L, calculated net

Your brief requires that estimated risk account for execution costs. For Indian intraday cash
equity this is not a rounding detail — at small position sizes it is the dominant term.

### Cost components, per round trip (intraday equity, NSE)

| Component | Basis | Applies |
|---|---|---|
| Brokerage | Angel One intraday rate (flat per executed order) | both legs |
| STT | 0.025% of turnover | **sell leg only** |
| Exchange transaction charge | NSE rate on turnover | both legs |
| SEBI turnover fee | ₹10 per crore | both legs |
| Stamp duty | 0.003% | **buy leg only** |
| GST | 18% on (brokerage + exchange charge + SEBI fee) | — |
| DP charges | — | not applicable intraday |

**Verify every rate against Angel One's live schedule before coding.** These change.

### Worked example — why this matters

₹50,000 capital, 0.5% risk per trade = ₹250 risk budget.
Stock at ₹500, stop at ₹495 → ₹5 risk/share → 50 shares → ₹25,000 position.

Approximate round-trip cost: **≈ ₹56.** That is **22% of your risk budget**, consumed before the
market moves at all.

Break-even win rate, net of that cost:

| Target | Gross break-even | **Net break-even** |
|---|---|---|
| 1R | 50.0% | **≈ 61%** |
| 2R | 33.3% | **≈ 41%** |
| 3R | 25.0% | **≈ 32%** |

A 1R intraday system needs to win roughly 61% of the time just to stand still. The repo's own
flagship ORB example produced 29.4% target-first vs 25.5% stop-first — a coin flip, gross.

**Two direct design consequences:**
1. Flat per-order brokerage dominates at small size. Very small positions are structurally
   uneconomic. Minimum position size should be a hard risk rule, not an afterthought.
2. Favour 2R+ targets. The net break-even gap narrows sharply as R rises.

### Where costs enter the code

- **Sizing:** `risk_per_share = (entry − stop) + per_share_cost_estimate + slippage_assumption`
- **Signal acceptance:** reject any signal whose net expectancy is not positive under the cost model
- **Backtest:** every trade debited at the same model; headline metrics reported net only
- **Live P&L:** realised P&L uses *actual* charges from the broker's trade book, not the estimate —
  and the gap between estimated and actual is itself logged and reported daily

### Risk state must survive restart

Daily loss limit, trade count, consecutive losses, open exposure — all persisted to SQLite and
reloaded on boot. An in-memory daily loss counter resets to zero on a crash, and a crash-loop at
11 AM would let the system trade straight through its own daily limit. Persist, reload, reconcile.

---

## 4. Scheduling the day (Asia/Kolkata)

| Time | Action |
|---|---|
| 08:45 | Service wakes. Authenticate (TOTP), fetch instrument master, load NSE holiday calendar. Abort if not a trading day. |
| 09:00 | Reconcile against broker. Verify flat. Compute risk budget from live equity. |
| 09:15 | Market open. **No entries** — opening-range observation only. |
| 09:30 | Opening range complete. Entry window opens. |
| 09:30–14:45 | Strategy loop on completed candles only. Signal → risk engine → order → broker-resident stop → monitor. |
| 14:45 | Entry window closes. Management of open positions only. |
| 15:15 | Hard square-off, supervisor-owned, limit ladder. |
| 15:35 | Reconcile final positions, compute net P&L from the trade book, write daily report, Telegram summary. |
| Continuous | Supervisor heartbeat check, orphan-position check, kill-switch watch. |

Cron/systemd timers trigger the lifecycle. The app itself does not rely on a human being present at
any point in that table.

---

## 5. Kill switch

A single flag in the DB plus a Telegram command, checked on every loop iteration and before every
order. When set: no new entries, cancel pending entry orders, **leave protective orders untouched**,
optionally flatten, alert. It must be settable from your phone and must take effect without a
restart. Protective stops are never cancelled during error recovery unless a verified replacement
is already confirmed live at the broker.

---

## 6. What automation does and does not buy you

It buys: consistency, no hesitation, no revenge trading, exact position sizing, limits that cannot
be talked out of, a complete audit trail, and the ability to walk away.

It does not buy an edge. An automated losing strategy loses faster and more reliably than a manual
one, because it never gets bored and never skips a bad setup. The ORB/VWAP/EMA family in the brief
are **unproven candidates**. Whether any of them survives Indian intraday costs is an open empirical
question that the backtester exists to answer — and a genuinely possible answer is "none of them,
at this capital level."

Per the brief, AUTO_EXECUTION stays disabled until: the backtester shows positive net expectancy
out-of-sample, forward paper trading confirms it across varied conditions, compliance is confirmed
with Angel One, the static IP is registered, and you explicitly enable it.

---

## 7. Build order

1. Cost model + Angel One rate schedule — *first*, because everything downstream depends on it
2. BrokerAdapter against SmartAPI, PAPER implementation first
3. Risk engine (pure, deterministic, persisted state)
4. Event-driven backtester with the cost model wired in; walk-forward + out-of-sample
5. **Gate: positive net expectancy out-of-sample, or stop here and reconsider**
6. Execution state machine, idempotency, reconciliation
7. Supervisor + heartbeat + kill switch
8. Telegram + daily reporting
9. VPS deploy, static IP registration, systemd
10. 30+ sessions forward paper on the VPS
11. **Gate: your explicit authorisation**, then LIVE_APPROVAL_REQUIRED at minimum size
12. AUTO_EXECUTION only after a separate review

---

## Sources

- NSE — FAQ, Safer participation of Retail investors in Algorithmic trading (03-11-2025):
  https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQ_Retail%20Algo_03112025_NSE.pdf
- SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013 (04-02-2025):
  https://www.cse-india.com/upload/upload/Feb_042025.pdf
- Angel One — SmartAPI changes from 1 April 2026:
  https://www.angelone.in/news/market-updates/what-s-changing-in-angel-one-s-smartapi-access-from-april-1-2026
- NSE circulars NSE/INVG/69255, NSE/INVG/70309 — to be read before go-live

**Not financial advice.** Most intraday traders lose money net of costs.
