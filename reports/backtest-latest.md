# Backtest report

Data: 2026-08-05 to 2026-10-30 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-06**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 68 | 33.8 | -4418.99 | -940.70 | 3478.29 | -64.99 | -0.296 | 0.4 | 5158.53 |
| in-sample | 40 | 25.0 | -4440.85 | -2344.50 | 2096.35 | -111.02 | -0.506 | 0.22 | 4540.49 |
| out-of-sample | 28 | 46.4 | 21.86 | 1403.80 | 1381.94 | 0.78 | 0.003 | 1.01 | 1060.68 |
| strategy: orb | 63 | 34.9 | -3973.92 | -740.10 | 3233.82 | -63.08 | -0.281 | 0.42 | 4713.46 |
| strategy: vwap_reclaim | 5 | 20.0 | -445.07 | -200.60 | 244.47 | -89.01 | -0.488 | 0.16 | 449.34 |

Exits: stop 27, square-off 39, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 226
- net reward:risk N below N: 210
- size is zero: stop too far for the risk budget: 185
- charges are N% of the risk budget (max N%): 94
- position N below the minimum N: 68
- net reward:risk -N below N: 20
- size is zero: no cash or position cap left for one share: 12
- daily loss limit: no room left (lost N, open risk N, limit N): 6

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
