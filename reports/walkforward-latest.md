# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -70.80 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-10-08 to 2026-10-22 | orb_low_stop | 45 | -0.355 | 14 | -85.41 | -0.382 |
| 2026-10-23 to 2026-11-05 | vwap_only | 20 | -0.431 | 10 | -59.73 | -0.244 |
| 2026-11-06 to 2026-11-20 | orb_low_stop | 50 | -0.242 | 16 | -64.92 | -0.314 |

All unseen trades: 40, net ₹-2831.85, avg -0.320R.
