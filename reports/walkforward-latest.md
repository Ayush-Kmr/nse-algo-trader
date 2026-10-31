# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -112.85 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-09-17 to 2026-09-30 | rs_filter | 19 | -0.189 | 12 | -150.25 | -0.649 |
| 2026-10-01 to 2026-10-15 | orb_low_stop | 39 | -0.298 | 16 | -82.46 | -0.379 |
| 2026-10-16 to 2026-10-30 | target_2r | 14 | -0.365 | 7 | -118.18 | -0.523 |

All unseen trades: 35, net ₹-3949.62, avg -0.500R.
