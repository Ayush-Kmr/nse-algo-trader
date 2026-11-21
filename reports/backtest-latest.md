# Backtest report

Data: 2026-08-25 to 2026-11-20 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-27**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: FAILS the gate: out-of-sample expectancy is -37.25 per trade after costs.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 85 | 34.1 | -5957.86 | -1728.35 | 4229.51 | -70.09 | -0.318 | 0.36 | 6187.47 |
| in-sample | 53 | 32.1 | -4765.70 | -2061.40 | 2704.30 | -89.92 | -0.403 | 0.26 | 5142.72 |
| out-of-sample | 32 | 37.5 | -1192.16 | 333.05 | 1525.21 | -37.25 | -0.176 | 0.58 | 1768.19 |
| strategy: orb | 80 | 35.0 | -5512.12 | -1527.15 | 3984.97 | -68.90 | -0.307 | 0.37 | 5741.73 |
| strategy: vwap_reclaim | 5 | 20.0 | -445.74 | -201.20 | 244.54 | -89.15 | -0.488 | 0.16 | 450.01 |

Exits: stop 35, square-off 48, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 324
- net reward:risk N below N: 270
- size is zero: stop too far for the risk budget: 225
- charges are N% of the risk budget (max N%): 178
- position N below the minimum N: 154
- net reward:risk -N below N: 27
- size is zero: no cash or position cap left for one share: 25
- daily loss limit: no room left (lost N, open risk N, limit N): 11

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
