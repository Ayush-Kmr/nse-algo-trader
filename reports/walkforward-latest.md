# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -98.27 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-09-17 to 2026-09-30 | orb_low_stop | 34 | -0.216 | 16 | -96.64 | -0.429 |
| 2026-10-01 to 2026-10-15 | orb_low_stop | 39 | -0.293 | 16 | -84.32 | -0.379 |
| 2026-10-16 to 2026-10-30 | target_2r | 14 | -0.365 | 8 | -129.43 | -0.583 |

All unseen trades: 40, net ₹-3930.74, avg -0.440R.
