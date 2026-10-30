# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -74.48 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-09-16 to 2026-09-29 | rs_filter | 16 | -0.186 | 12 | -134.67 | -0.567 |
| 2026-09-30 to 2026-10-14 | orb_low_stop | 39 | -0.301 | 16 | -80.24 | -0.362 |
| 2026-10-15 to 2026-10-29 | orb_low_stop | 45 | -0.396 | 17 | -26.58 | -0.113 |

All unseen trades: 45, net ₹-3351.71, avg -0.322R.
