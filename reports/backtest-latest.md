# Backtest report

Data: 2026-08-05 to 2026-10-30 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-06**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 68 | 33.8 | -4361.85 | -874.00 | 3487.85 | -64.14 | -0.296 | 0.41 | 5101.39 |
| in-sample | 40 | 25.0 | -4440.85 | -2344.50 | 2096.35 | -111.02 | -0.506 | 0.22 | 4540.49 |
| out-of-sample | 28 | 46.4 | 79.00 | 1470.50 | 1391.50 | 2.82 | 0.003 | 1.05 | 1003.54 |
| strategy: orb | 63 | 34.9 | -3916.78 | -673.40 | 3243.38 | -62.17 | -0.281 | 0.42 | 4656.32 |
| strategy: vwap_reclaim | 5 | 20.0 | -445.07 | -200.60 | 244.47 | -89.01 | -0.488 | 0.16 | 449.34 |

Exits: stop 27, square-off 39, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 226
- net reward:risk N below N: 211
- size is zero: stop too far for the risk budget: 176
- charges are N% of the risk budget (max N%): 98
- position N below the minimum N: 68
- net reward:risk -N below N: 20
- size is zero: no cash or position cap left for one share: 17
- daily loss limit: no room left (lost N, open risk N, limit N): 6

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
