# Backtest report

Data: 2026-08-18 to 2026-11-13 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-19**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 29 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 79 | 34.2 | -5317.45 | -1292.65 | 4024.80 | -67.31 | -0.296 | 0.38 | 5708.08 |
| in-sample | 50 | 30.0 | -4467.24 | -1890.75 | 2576.49 | -89.34 | -0.390 | 0.28 | 4857.87 |
| out-of-sample | 29 | 41.4 | -850.21 | 598.10 | 1448.31 | -29.32 | -0.132 | 0.65 | 1301.29 |
| strategy: orb | 75 | 34.7 | -5023.57 | -1186.10 | 3837.47 | -66.98 | -0.293 | 0.39 | 5414.20 |
| strategy: vwap_reclaim | 4 | 25.0 | -293.88 | -106.55 | 187.33 | -73.47 | -0.337 | 0.23 | 299.69 |

Exits: square-off 46, stop 31, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 286
- size is zero: stop too far for the risk budget: 242
- net reward:risk N below N: 204
- charges are N% of the risk budget (max N%): 94
- position N below the minimum N: 80
- size is zero: no cash or position cap left for one share: 24
- daily loss limit: no room left (lost N, open risk N, limit N): 24
- net reward:risk -N below N: 21

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
