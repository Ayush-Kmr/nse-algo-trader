# Backtest report

Data: 2026-08-31 to 2026-11-27 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-11-02**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 88 | 33.0 | -6756.08 | -2385.20 | 4370.88 | -76.77 | -0.345 | 0.31 | 6975.49 |
| in-sample | 60 | 33.3 | -4263.51 | -1181.50 | 3082.01 | -71.06 | -0.309 | 0.34 | 5122.82 |
| out-of-sample | 28 | 32.1 | -2492.57 | -1203.70 | 1288.87 | -89.02 | -0.420 | 0.27 | 2492.57 |
| strategy: orb | 84 | 33.3 | -6459.49 | -2276.55 | 4182.94 | -76.90 | -0.345 | 0.32 | 6678.90 |
| strategy: vwap_reclaim | 4 | 25.0 | -296.59 | -108.65 | 187.94 | -74.15 | -0.338 | 0.23 | 299.69 |

Exits: square-off 49, stop 37, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 334
- net reward:risk N below N: 286
- size is zero: stop too far for the risk budget: 243
- charges are N% of the risk budget (max N%): 198
- position N below the minimum N: 166
- net reward:risk -N below N: 28
- size is zero: no cash or position cap left for one share: 26
- daily loss limit: no room left (lost N, open risk N, limit N): 12

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
