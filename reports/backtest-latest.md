# Backtest report

Data: 2026-08-04 to 2026-10-29 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-05**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.05% slippage.

**Verdict: FAILS the gate: out-of-sample expectancy is -7.15 per trade after costs.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 70 | 37.1 | -4067.81 | -422.85 | 3644.96 | -58.11 | -0.269 | 0.45 | 4816.82 |
| in-sample | 39 | 30.8 | -3846.04 | -1771.50 | 2074.54 | -98.62 | -0.448 | 0.27 | 4012.33 |
| out-of-sample | 31 | 45.2 | -221.77 | 1348.65 | 1570.42 | -7.15 | -0.045 | 0.9 | 1147.62 |
| strategy: orb | 65 | 38.5 | -3660.12 | -258.70 | 3401.42 | -56.31 | -0.254 | 0.47 | 4409.13 |
| strategy: vwap_reclaim | 5 | 20.0 | -407.69 | -164.15 | 243.54 | -81.54 | -0.464 | 0.18 | 423.19 |

Exits: stop 29, square-off 38, target 2, target (gap) 1

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 225
- net reward:risk N below N: 190
- size is zero: stop too far for the risk budget: 145
- charges are N% of the risk budget (max N%): 81
- position N below the minimum N: 57
- size is zero: no cash or position cap left for one share: 55
- net reward:risk -N below N: 20
- daily loss limit: no room left (lost N, open risk N, limit N): 2

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
