# Backtest report

Data: 2026-08-04 to 2026-10-28 (59 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-01**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.05% slippage.

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 71 | 31.0 | -5187.99 | -1703.85 | 3484.14 | -73.07 | -0.363 | 0.33 | 5476.00 |
| in-sample | 43 | 30.2 | -3349.47 | -1247.50 | 2101.97 | -77.89 | -0.388 | 0.33 | 3580.50 |
| out-of-sample | 28 | 32.1 | -1838.52 | -456.35 | 1382.17 | -65.66 | -0.324 | 0.34 | 1895.50 |
| strategy: orb | 67 | 32.8 | -4616.61 | -1304.35 | 3312.26 | -68.90 | -0.334 | 0.36 | 4904.62 |
| strategy: vwap_reclaim | 4 | 0.0 | -571.38 | -399.50 | 171.88 | -142.84 | -0.852 | 0.0 | 571.38 |

Exits: stop 32, square-off 38, target 1

Top reasons the risk engine blocked a signal:

- net reward:risk N below N: 232
- max open positions (N) reached: 216
- size is zero: stop too far for the risk budget: 141
- daily loss limit: no room left (lost N, open risk N, limit N): 4
- charges are N% of the risk budget (max N%): 4
- max trades per day (N) reached: 2

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
