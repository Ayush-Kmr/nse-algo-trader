# Backtest report

Data: 2026-08-05 to 2026-10-29 (59 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-05**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 67 | 32.8 | -4523.25 | -1089.45 | 3433.80 | -67.51 | -0.300 | 0.38 | 5129.40 |
| in-sample | 39 | 25.6 | -3963.54 | -1929.35 | 2034.19 | -101.63 | -0.451 | 0.25 | 4072.25 |
| out-of-sample | 28 | 42.9 | -559.71 | 839.90 | 1399.61 | -19.99 | -0.090 | 0.72 | 1067.46 |
| strategy: orb | 63 | 33.3 | -4227.83 | -981.25 | 3246.58 | -67.11 | -0.297 | 0.39 | 4833.98 |
| strategy: vwap_reclaim | 4 | 25.0 | -295.42 | -108.20 | 187.22 | -73.85 | -0.338 | 0.23 | 299.69 |

Exits: stop 26, square-off 39, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 225
- net reward:risk N below N: 210
- size is zero: stop too far for the risk budget: 169
- charges are N% of the risk budget (max N%): 95
- position N below the minimum N: 76
- net reward:risk -N below N: 20
- size is zero: no cash or position cap left for one share: 14
- daily loss limit: no room left (lost N, open risk N, limit N): 12

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
