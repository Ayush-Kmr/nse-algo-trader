# Backtest report

Data: 2026-08-12 to 2026-11-06 (60 sessions), 5-minute bars, Yahoo Finance. Out-of-sample from **2026-10-13**.
Strategies: orb, vwap_reclaim. Capital 50000, risk 0.5%/trade, daily limit 1.0%. All figures **net** of Angel One charges and 0.06% per fill (slippage + half spread).

**Verdict: FAILS the gate: out-of-sample expectancy is -3.54 per trade after costs.**

| slice | trades | win % | net ₹ | gross ₹ | charges ₹ | ₹/trade | avg R | PF | max DD ₹ |
|---|---|---|---|---|---|---|---|---|---|
| all | 74 | 36.5 | -4576.21 | -808.65 | 3767.56 | -61.84 | -0.277 | 0.41 | 5281.88 |
| in-sample | 41 | 26.8 | -4459.40 | -2346.20 | 2113.20 | -108.77 | -0.488 | 0.19 | 4717.22 |
| out-of-sample | 33 | 48.5 | -116.81 | 1537.55 | 1654.36 | -3.54 | -0.016 | 0.95 | 1180.97 |
| strategy: orb | 69 | 37.7 | -4129.30 | -607.00 | 3522.30 | -59.84 | -0.262 | 0.43 | 4834.97 |
| strategy: vwap_reclaim | 5 | 20.0 | -446.91 | -201.65 | 245.26 | -89.38 | -0.488 | 0.16 | 450.01 |

Exits: square-off 43, stop 29, target 2

Top reasons the risk engine blocked a signal:

- max open positions (N) reached: 266
- net reward:risk N below N: 226
- size is zero: stop too far for the risk budget: 193
- charges are N% of the risk budget (max N%): 125
- position N below the minimum N: 104
- size is zero: no cash or position cap left for one share: 26
- net reward:risk -N below N: 21
- daily loss limit: no room left (lost N, open risk N, limit N): 11

60 days of 5-minute data is a short sample. Treat any result as a hypothesis, not proof.
