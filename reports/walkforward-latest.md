# Walk-forward

Train on 30 sessions, pick the best variant by avg R, trade it on the next 10, roll on. Net of costs.

**Verdict: FAILS the gate: out-of-sample expectancy is -76.49 per trade after costs.**

| test window | picked | train trades | train avg R | test trades | test ₹/trade | test avg R |
|---|---|---|---|---|---|---|
| 2026-09-30 to 2026-10-14 | orb_low_stop | 39 | -0.305 | 16 | -80.09 | -0.361 |
| 2026-10-15 to 2026-10-29 | target_2r | 13 | -0.362 | 9 | -96.59 | -0.428 |
| 2026-10-30 to 2026-11-13 | baseline | 45 | -0.310 | 17 | -62.47 | -0.288 |

All unseen trades: 42, net ₹-3212.76, avg -0.346R.
