# nse-algo-trader — notes for Claude

## Project skills (`.claude/skills/`)

- **NSE analysis frameworks** (from Bhala-Srinivash/nse-trading-skills, MIT): `nse-trading-toolkit` (orchestrator), `technical-analysis`, `multi-timeframe-analysis`, `rsi-divergence`, `fibonacci-trading`, `stop-loss-strategies`, `trailing-stops`, `position-sizing`, `risk-reward-ratio`. Prompt-only, no code.
- **Audit skills** (from tradermonty/claude-trading-skills): `backtest-expert`, `edge-strategy-reviewer`, `residual-edge-analyzer`, `signal-postmortem`, `drawdown-circuit-breaker`, `pre-trade-discipline-gate`, `position-sizer`, `trade-performance-coach`.

## Rules when using them

- Charges: use this repo's AngelOne cost model, not the toolkit's "~0.1% for delivery" rule of thumb. Intraday charges have been about 2x the gross loss here.
- Any setup the frameworks suggest (divergence, fib, MTF confluence...) counts as a hypothesis. It must clear `python -m algo signals` (beat +0.28R gross) before it goes near the engine. See docs/RESEARCH_LOG.md.
- Data: Yahoo `.NS` symbols or SmartAPI candles. The Groww MCP the toolkit mentions is not configured (it can place orders on a real account).
- Analysis output is never a buy/sell recommendation. The engine is PAPER only.
