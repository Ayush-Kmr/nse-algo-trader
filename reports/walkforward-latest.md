# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -78.51 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-09-24 to 2026-10-08 | orb_low_stop | 37 | -0.269 | 15 | -114.90 | -0.515 |
| 2026-10-09 to 2026-10-23 | orb_low_stop | 43 | -0.368 | 14 | -84.73 | -0.382 |
| 2026-10-26 to 2026-11-06 | vwap_only | 20 | -0.431 | 11 | -20.97 | -0.080 |

All unseen trades: 40, net ₹-3140.48, avg -0.349R.
