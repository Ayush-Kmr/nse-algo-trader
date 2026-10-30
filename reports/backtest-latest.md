# Backtest report

Data: 2026-08-04 to 2026-10-29 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-05**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 66 | 33.3 | -4504.31 | -1121.95 | 3382.36 | -68.25 | -0.315 | 0.38 | 5101.39 |
| in-sample | 38 | 26.3 | -4008.03 | -2021.45 | 1986.58 | -105.47 | -0.480 | 0.24 | 4107.67 |
| out-of-sample | 28 | 42.9 | -496.28 | 899.50 | 1395.78 | -17.72 | -0.091 | 0.75 | 1003.54 |
| strategy: orb | 61 | 34.4 | -4059.24 | -921.35 | 3137.89 | -66.54 | -0.301 | 0.4 | 4656.32 |
| strategy: vwap_reclaim | 5 | 20.0 | -445.07 | -200.60 | 244.47 | -89.01 | -0.488 | 0.16 | 449.34 |

Exits: stop 27, square-off 37, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 213
- net reward:risk N below N: 210
- size is zero: stop too far for the risk budget: 163
- charges are N% of the risk budget (max N%): 98
- position N below the minimum N: 68
- net reward:risk -N below N: 20
- size is zero: no cash or position cap left for one share: 17
- daily loss limit: no room left (lost N, open risk N, limit N): 6

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
