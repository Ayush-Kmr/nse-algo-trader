# Backtest report

Data: 2026-08-04 to 2026-10-28 (59 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-01**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.05% slippage.

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 70 | 31.4 | -5140.76 | -1739.20 | 3401.56 | -73.44 | -0.367 | 0.32 | 5267.77 |
| in-sample | 42 | 31.0 | -3488.00 | -1438.65 | 2049.35 | -83.05 | -0.414 | 0.29 | 3558.03 |
| out-of-sample | 28 | 32.1 | -1652.76 | -300.55 | 1352.21 | -59.03 | -0.296 | 0.36 | 1709.74 |
| strategy: orb | 66 | 33.3 | -4747.61 | -1489.20 | 3258.41 | -71.93 | -0.349 | 0.33 | 4874.62 |
| strategy: vwap_reclaim | 4 | 0.0 | -393.15 | -250.00 | 143.15 | -98.29 | -0.657 | 0.0 | 393.15 |

Exits: stop 31, square-off 38, target 1

Top reasons the risk engine blocked a signal:

- net reward:risk N below N: 236
- max open positions (N) reached: 205
- size is zero: stop too far for the risk budget: 129
- daily loss limit: no room left (lost N, open risk N, limit N): 3
- charges are N% of the risk budget (max N%): 3
- max trades per day (N) reached: 2

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
