# Phase 0 + Phase 1 — Discovery & Repository Audit

Date: 2026-10-29
Repo audited: https://github.com/jakeschincariol/day-trader-skill @ `3d0f4ef` (single commit, 2026-10-20)
Status: **Phase 1 deliverable — awaiting review. No code modified, no orders anywhere.**

---

## 1. Phase 0 — answers on record

| # | Question | Answer |
|---|---|---|
| 1 | Broker | **Angel One SmartAPI** |
| 3 | Instruments | **Intraday cash equity (NSE)** |
| 6 | Execution model | **Approval-required, permanently.** No auto-execution target. |
| 7 | Hosting | **Laptop (macOS)** — see §4, this has a hard regulatory consequence |

### Still unanswered (blocking parts of Phase 2)

2. Trading capital in INR
4. Max acceptable loss per trade
5. Max acceptable daily loss
8. Do you have a SmartAPI key provisioned, and a **registered static IP**?
9. Historical data source for backtesting — SmartAPI `getCandleData`, or something else?
10. Your experience with slippage, drawdown, and intraday leverage

Until answered, simulation-only defaults from the brief apply (₹50,000 notional, 0.5%/trade, 1%/day, max 2 positions, no leverage, no shorting, no F&O, no overnight, flat before close, Asia/Kolkata).

### Conflict with existing folder contents

This folder already contains `nifty_strategy.py` + `README.md`: a **Zerodha Kite, Nifty 50 ATM options** system sized for ₹10,000. That contradicts today's answers (Angel One, cash equity). **Unresolved — needs a decision (see §7).**

---

## 2. What the repo actually is

This is the single most important finding, and it reframes the whole plan.

`day-trader-skill` is **not an application**. It is a Claude Code **plugin containing 11 skills**: eleven `SKILL.md` instruction files plus eleven standalone Python CLI scripts, with no package, no entry point, no daemon, no scheduler, no database and no event loop. State is passed between steps as JSON files in a `trader/` folder. Claude is the orchestrator: a human drives a chat, Claude runs one script, reads the JSON, runs the next.

Its own `trader-broker/SKILL.md` states the design intent explicitly:

> "Never places orders from a scheduled or background task: nobody is there to say yes."

**Consequence:** the repo cannot satisfy objectives 6, 7, 13 of your brief (continuous position monitoring, stop/trailing/target management, scheduled unattended operation), and it structurally violates your rule *"Protective stops and emergency exit handling must not depend on Claude being online."* In this design, Claude being online is the only thing that advances a trade.

That is not a defect in the repo — it is a deliberate safety posture, and a defensible one. It is simply a different product from the one you specified.

### Secondary structural facts

- **Zero third-party dependencies.** Pure Python 3.8+ stdlib throughout. No pandas, no numpy.
- **Single commit, 9 days old, one author.** No issue history, no release history, no CI config. No evidence of maintenance.
- **No `eval`, `exec`, or `pickle`.** One `subprocess` call, to `pdftotext`, in the Congress-disclosure module. **Security posture: clean.** No credential handling in code at all — keys live in the Claude Desktop MCP config and are never read by these scripts.
- **Test suite exists** (12 files, offline fixtures). **I did not execute it** — the sandbox blocked running third-party code, consistent with your rule not to blindly execute third-party scripts. Test pass status is therefore **unverified**.

---

## 3. Compatibility matrix

| Module | LOC | Verdict | Detail |
|---|---|---|---|
| `trader-risk` | 819 | **Port the logic** | The strongest asset in the repo. Sequential batch evaluation (each order checked as if prior ones filled), entry/exit asymmetry (exits are never blocked by day limits — correct and important), measures risk from the *higher* of plan entry and a fresh price, 15-minute staleness guard, fingerprinted verdicts so the broker step can only act on a PASS for that exact order. US-coupled: NYSE holiday table, NY timezone, PDT guard, US ticker validation, Alpaca-specific format rules. **Rewrite the rules in a Pydantic/typed engine; keep the design.** |
| `trader-budget` | 881 | **Port the logic** | `Decimal` arithmetic, floor rounding, takes the *minimum* across max-loss / cash-buffer / position-cap / order-cap constraints. Sound. **Gap:** risk-per-share is `entry − stop` with **no cost or slippage term**, which your Phase 5 explicitly requires. |
| `trader-exit` | 735 | **Port partially** | Stop/target geometry, R-multiples, and a useful guard rejecting stops tighter than 0.05% of price (inside the spread). Rule library is US-intraday-shaped but transferable. |
| `trader-entry` | 960 | **Rewrite** | Logic (completed-candle ORB trigger detection) is reusable; its data layer is Yahoo Finance. |
| `trader-scanner` | 1083 | **Rewrite** | Universe comes from Nasdaq Trader symbol files; bars from Yahoo. Entirely US. Scan *patterns* (ORB, flags, oversold bounce) are reusable as specifications. |
| `trader-timemachine` | 956 | **Do not use as a validator** | See §3a. |
| `trader-broker` | 720 | **Discard** | Alpaca/IBKR-shaped. Notably `ticket.py` never contacts a broker at all — Claude makes the MCP call. There is no `BrokerAdapter` here to extend. |
| `trader-alerts` | 787 | **Discard** | Polls Yahoo/Stooq; replaced by a proper monitor loop. |
| `trader-news` | 546 | **Discard** | Yahoo RSS + SEC EDGAR. No Indian equivalent. |
| `trader-analyst` | 548 | **Discard** | SEC XBRL `companyfacts`. US-only. |
| `trader-pelosi` | 566 | **Discard** | US House Clerk disclosures. No analogue. |

**Reusable: ~2,400 LOC of risk/sizing/exit logic as a specification. Directly runnable against NSE: none.**

### 3a. Backtesting assessment — the critical gap

Your Phase 4 lists fourteen requirements. Measured against them:

| Requirement | Present? |
|---|---|
| Look-ahead bias prevention | **Yes** — completed candles only, live in-progress bar excluded, pool restricted to sessions strictly before the plan date. Genuinely careful. |
| Deterministic / reproducible | **Yes** — seeded RNG (default 19), documented, reproducible across machines. |
| Realistic brokerage & charges | **No** |
| STT and taxes | **No** |
| Slippage | **No** |
| Bid-ask spread | **No** |
| Market impact | **No** |
| Corporate-action adjustment | **No** |
| Survivorship bias evaluation | **No** |
| Walk-forward testing | **No** |
| Out-of-sample validation | **No** |
| Parameter sensitivity | **No** |

A repo-wide grep for `slippage|commission|brokerage|fee|STT|impact` returns **no cost model anywhere in the codebase.** Every R-multiple it reports is gross.

This matters disproportionately for Indian intraday cash equity. A round trip carries brokerage, STT on the sell leg, exchange transaction charges, SEBI turnover fee, stamp duty and GST. On a position of a few thousand rupees with a 1R target, costs can consume a meaningful fraction of the edge. A gross backtest showing a thin positive expectancy is consistent with a net-negative strategy.

Additionally, the Time Machine is a **bootstrap resampler**, not a backtester. It draws 5-minute bars IID from the same time-of-day bucket over 60 sessions. That destroys autocorrelation, volatility clustering and trend persistence — the exact properties a momentum strategy like ORB depends on. **It systematically misprices trend-following setups.** Its own README is honest about being a simulation; your brief already says not to treat 10,000 paths as proof. I'd go further: **do not use it as a validation gate at all.** Build a real event-driven backtester.

The repo's own worked example is instructive: the TSLA ORB trade it ships as a demo came out at 29.4% target-first vs 25.5% stop-first at 1R — a coin flip, before costs. That is the honest baseline for this setup family.

---

## 4. Regulatory findings — these change your architecture

Verified against Angel One's published guidance (sources at end). **Confirm each with Angel One directly before going live; I am not a compliance advisor.**

1. **Static IP is mandatory.** From 1 April 2026, Angel One accepts API order execution **only from a registered primary static IP**, registered in the SmartAPI dashboard under "Add App". A secondary backup IP is allowed. Mapping can change at most **once per calendar week**. One IP maps to one client.

   > **This conflicts with your hosting answer.** A MacBook on home or office broadband has a dynamic IP. Development and paper trading on the laptop are fine. **Live order placement from it is not viable** without a static IP — either a static-IP VPS, or a static-IP proxy service.

2. **Market orders are prohibited for algorithmic trading.** IOC orders too. Every entry and every exit must be LIMIT or STOPLOSS-LIMIT. This invalidates the repo's market-order bracket pattern *and* its market-order flatten pattern, and it means **your square-off logic needs a marketable-limit design with a re-price ladder**, not a market order.

3. **10 orders/second threshold.** Below it, no individual exchange algo registration — a generic exchange algo ID applies. Your strategy will run at a handful of orders per *day*, so this is not a constraint, but orders must still be correctly tagged.

4. **Unresolved — needs confirmation from Angel One:** whether an order you personally approve one-by-one in a dashboard is classified as a *manual API order* or an *algo order*. Your chosen approval-required model sits exactly on this line. The answer determines whether the static IP and algo-tagging rules bind you at all. **Do not assume the favourable reading.**

---

## 5. SmartAPI capability notes (partially verified)

Confirmed from the official Python SDK: `placeOrder` takes `variety`, `tradingsymbol`, `symboltoken`, `transactiontype`, `exchange`, `ordertype`, `producttype` (`INTRADAY` for MIS), `duration`, `price`, `quantity`, and `squareoff` / `stoploss` fields. WebSocket v2 exists for live feeds, plus a separate order-update socket. `getfeedToken()`, `terminateSession()`, GTT and historical-candle endpoints exist.

**Unverified and must be confirmed against live docs in Phase 2 before the adapter is written:**
- Exact `variety` enum values, and whether ROBO (bracket) is available via API for cash intraday
- Whether broker-native ROBO survives a client disconnect (**the single most important question in this whole project** — see §6)
- Order modify/cancel endpoint signatures
- Published rate limits per endpoint
- Token/session lifetime and TOTP refresh semantics

---

## 6. Proposed architecture

A standalone Python service. Claude is a **reasoning layer bolted on the side**, never in the execution path.

```
                        ┌──────────────────────────────┐
                        │  Claude (advisory only)      │
                        │  pre-market notes, signal    │
                        │  explanations, post-mortems, │
                        │  daily report prose          │
                        └──────────────┬───────────────┘
                                       │ reads DB, writes reports
                                       │ CANNOT create or alter orders
  ┌────────────────────────────────────┴────────────────────────────────┐
  │                      trading service (FastAPI + asyncio)            │
  │                                                                     │
  │  market data ──► strategy ──► signal ──► RISK ENGINE ──► approval   │
  │  (SmartAPI       (ORB,        (typed,    (deterministic, queue      │
  │   WS v2 +         VWAP,        schema-    no LLM, hard        │     │
  │   candles)        EMA)         bound)     BLOCK)              │     │
  │                                                               ▼     │
  │  position monitor ◄──── execution engine (state machine) ◄── you    │
  │  (reconciles with broker,     LIMIT / SL-L only                tap  │
  │   never trusts local state)   idempotency keys                 yes  │
  │                               partial-fill handling                 │
  └────────────────────────┬────────────────────────────────────────────┘
                           │
          SQLite (WAL) ────┴──── Telegram bot ──── local dashboard
          every order, fill,     approvals +       (FastAPI + HTMX)
          verdict, P&L           alerts
```

**Design commitments**

- **Protective exits are broker-side wherever SmartAPI supports it.** If broker-native ROBO is unavailable or does not survive disconnect, that is a *blocking finding*, and the mitigation is a separate supervisor process with its own session, its own heartbeat, and a hard flatten — not a `while` loop inside the main app. I will not design a locally-managed stop and present it as equivalent protection.
- **Risk engine is pure, synchronous, deterministic, and has no LLM and no network.** It is the most-tested module in the system. A BLOCK is final and unappealable by any other component.
- **Costs are first-class.** A `CostModel` for Angel One (brokerage, STT, exchange charges, SEBI fee, stamp duty, GST) is built in Phase 2 — *before* the backtester — and feeds both position sizing and backtest P&L. Every expectancy figure will be net.
- **Reconcile before trade.** On every startup, and before every new entry, the engine pulls live positions and orders from the broker and reconciles against the DB. Local state is never authoritative.
- **No market orders anywhere.** Marketable-limit with a bounded re-price ladder, plus an explicit unfilled-at-square-off escalation path.

**Proposed layout**

```
trading/
  config/        settings.py (pydantic-settings), .env.example, strategies.yaml
  broker/        base.py (BrokerAdapter ABC), angelone.py, paper.py, models.py
  data/          feed.py (WS v2), candles.py, universe.py, calendar.py (NSE holidays)
  strategy/      base.py, orb.py, vwap_trend.py, ema_trend.py, signal.py
  risk/          engine.py, rules.py, sizing.py, costs.py, killswitch.py
  execution/     state_machine.py, order_manager.py, reconciler.py, square_off.py
  backtest/      engine.py, costs.py, walkforward.py, metrics.py
  monitor/       position_monitor.py, supervisor.py
  notify/        telegram.py, templates.py
  api/           app.py, routes/, auth.py
  reporting/     daily.py, claude_layer.py
  storage/       db.py, models.py, migrations/
tests/           unit/, integration/, scenarios/
```

**Modes:** `READ_ONLY` → `PAPER` (default) → `LIVE_APPROVAL_REQUIRED` → `AUTO_EXECUTION` (not built; a stub that raises).

---

## 7. Decisions I need from you

1. **Instrument conflict.** You answered *intraday cash equity on Angel One*. This folder holds a *Nifty 50 ATM options on Zerodha* system. Archive the old one and start clean, or did you intend to carry it forward?
2. **Static IP.** Live trading from a dynamic-IP laptop is not viable. Static-IP VPS, static-IP proxy, or stay in PAPER indefinitely on the laptop?
3. **Capital, per-trade loss cap, daily loss cap** (Phase 0 questions 2, 4, 5).
4. **Historical data** for the backtester — SmartAPI `getCandleData`, or another licensed source?
5. **Scope confirmation.** Do you want me to build this as a fresh application (my recommendation), rather than forking `day-trader-skill`?

---

## 8. Unresolved / unverified register

| Item | Status |
|---|---|
| Repo test suite passes | **Unverified** — execution blocked by sandbox |
| Broker-native ROBO survives client disconnect | **Unverified — blocking for LIVE** |
| SmartAPI `variety` enum, modify/cancel signatures, rate limits | **Unverified** |
| Whether per-order human approval exempts you from algo/static-IP rules | **RESOLVED 2026-10-29 — it does not.** NSE retail-algo FAQ: "all orders received via API from clients are considered Algo orders". See `UNATTENDED_DESIGN.md` §0. |
| Angel One exact intraday cost schedule | **Unverified** |
| Current NSE intraday margin rules for cash equity | **Unverified** |

---

## Sources

- Angel One — What's Changing in SmartAPI Access from April 1, 2026: https://www.angelone.in/news/market-updates/what-s-changing-in-angel-one-s-smartapi-access-from-april-1-2026
- SmartAPI Developer Portal: https://smartapi.angelbroking.com/docs
- SmartAPI Python SDK: https://github.com/angel-one/smartapi-python
- SmartAPI exchange regulations: https://smartapi.angelone.in/exchange-regulations
- Repository audited: https://github.com/jakeschincariol/day-trader-skill

**Not financial advice.** Nothing here establishes that any strategy named in this document is profitable. Most intraday traders lose money net of costs.
