# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: INCONCLUSIVE: 28 out-of-sample trades, need 30+ before any conclusion.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-09-17 to 2026-09-30 | rs_filter | 19 | -0.189 | 12 | -150.25 | -0.649 |
| 2026-10-01 to 2026-10-15 | orb_low_stop | 39 | -0.298 | 16 | -82.46 | -0.379 |

All unseen trades: 28, net ₹-3122.34, avg -0.495R.
