# Backtest report

Data: 2026-08-05 to 2026-10-30 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-06**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 69 | 33.3 | -4380.79 | -841.50 | 3539.29 | -63.49 | -0.282 | 0.41 | 5129.40 |
| in-sample | 41 | 24.4 | -4396.36 | -2252.40 | 2143.96 | -107.23 | -0.478 | 0.23 | 4505.07 |
| out-of-sample | 28 | 46.4 | 15.57 | 1410.90 | 1395.33 | 0.56 | 0.004 | 1.01 | 1067.46 |
| strategy: orb | 65 | 33.8 | -4085.37 | -733.30 | 3352.07 | -62.85 | -0.279 | 0.42 | 4833.98 |
| strategy: vwap_reclaim | 4 | 25.0 | -295.42 | -108.20 | 187.22 | -73.85 | -0.338 | 0.23 | 299.69 |

Exits: stop 26, square-off 41, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 238
- net reward:risk N below N: 211
- size is zero: stop too far for the risk budget: 182
- charges are N% of the risk budget (max N%): 95
- position N below the minimum N: 76
- net reward:risk -N below N: 20
- size is zero: no cash or position cap left for one share: 14
- daily loss limit: no room left (lost N, open risk N, limit N): 12

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
