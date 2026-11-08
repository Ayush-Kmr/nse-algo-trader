# Claude Code skills for this repo

These load automatically when Claude Code runs from the repo root. They are prompt-only: no code, no network calls. The usage rules are in `../../CLAUDE.md`.

## NSE analysis frameworks

Source: [Bhala-Srinivash/nse-trading-skills](https://github.com/Bhala-Srinivash/nse-trading-skills) (MIT, see `nse-trading-toolkit/LICENSE.upstream`). Added 2026-11-08.

| Skill | Use it for |
|---|---|
| `nse-trading-toolkit` | Full stock analysis that pulls in the skills below |
| `technical-analysis` | Trend, support/resistance, volume, indicator dashboard, scenarios |
| `multi-timeframe-analysis` | Weekly/daily/hourly 3-screen method, confluence score |
| `rsi-divergence` | Regular and hidden RSI divergence with confirmation rules |
| `fibonacci-trading` | Retracement entry zones, extension targets |
| `stop-loss-strategies` | Structure, ATR, S/R and moving-average stops |
| `trailing-stops` | ATR, structure, MA and chandelier trails |
| `position-sizing` | Fixed fractional, ATR and Kelly sizing |
| `risk-reward-ratio` | R:R, minimum R:R by win rate, expected value |

## Audit and discipline

Source: [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills). Added 2026-11-05.

| Skill | Use it for |
|---|---|
| `backtest-expert` | Checking backtest method and robustness |
| `edge-strategy-reviewer` | Scoring a strategy idea for real edge before building it |
| `residual-edge-analyzer` | Whether an edge survives costs and known factors |
| `signal-postmortem` | Reviewing what happened after signals fired |
| `drawdown-circuit-breaker` | Drawdown limits and when to stop trading |
| `pre-trade-discipline-gate` | Pre-trade checklist |
| `position-sizer` | Risk-based share sizing |
| `trade-performance-coach` | Reviewing closed trades for process mistakes |

## Ground rules

- Any setup these skills suggest is a hypothesis. It must beat +0.28R gross in `python3 -m algo signals` first (see `docs/RESEARCH_LOG.md`).
- Charges come from this repo's cost model, not the toolkit's ~0.1% shortcut.
- The Groww MCP the toolkit mentions is not configured, because it can place real orders.
