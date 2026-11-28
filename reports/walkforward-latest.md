# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -69.23 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-10-14 to 2026-10-28 | target_2r | 13 | -0.362 | 7 | -95.81 | -0.400 |
| 2026-10-29 to 2026-11-12 | orb_low_stop | 46 | -0.371 | 19 | -30.76 | -0.155 |
| 2026-11-13 to 2026-11-27 | baseline | 48 | -0.216 | 14 | -108.16 | -0.519 |

All unseen trades: 40, net ₹-2769.34, avg -0.325R.
