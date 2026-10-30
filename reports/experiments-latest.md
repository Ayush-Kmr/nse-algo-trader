# Experiments

Data 2026-08-05 to 2026-10-29 (59 sessions). In-sample before 2026-10-05, out-of-sample from it. All figures net of costs.
Pick on **in-sample** ₹/trade; read out-of-sample only as confirmation.

Gate: 30+ out-of-sample trades and a lower bound on avg R above zero, corrected for 12 variants.

| variant | IS trades | IS win% | IS ₹/trade | IS avg R | OOS trades | OOS win% | OOS ₹/trade | OOS avg R | all net ₹ | charges ₹ | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 38 | 26.3 | -105.47 | -0.480 | 28 | 42.9 | -17.72 | -0.091 | -4504.31 | 3382.36 | INCONCLUSIVE |
| target_2r | 8 | 25.0 | -143.26 | -0.608 | 15 | 20.0 | -75.09 | -0.357 | -2272.35 | 1014.70 | INCONCLUSIVE |
| breakeven_1r | 39 | 25.6 | -102.52 | -0.475 | 30 | 33.3 | -23.92 | -0.124 | -4715.72 | 3489.17 | FAILS |
| trail_1r | 40 | 25.0 | -101.80 | -0.470 | 31 | 35.5 | -26.39 | -0.134 | -4890.13 | 3582.63 | FAILS |
| let_run | 58 | 20.7 | -97.28 | -0.489 | 23 | 34.8 | -30.93 | -0.166 | -6353.68 | 4071.08 | INCONCLUSIVE |
| rs_filter | 32 | 25.0 | -100.43 | -0.431 | 18 | 44.4 | -2.83 | -0.004 | -3264.85 | 2534.25 | INCONCLUSIVE |
| orb_only | 38 | 26.3 | -104.41 | -0.463 | 26 | 42.3 | -26.13 | -0.126 | -4646.77 | 3305.12 | INCONCLUSIVE |
| vwap_only | 8 | 12.5 | -165.08 | -0.691 | 14 | 35.7 | -39.64 | -0.170 | -1875.63 | 1188.53 | INCONCLUSIVE |
| orb_30m | 43 | 18.6 | -116.69 | -0.549 | 25 | 28.0 | -61.82 | -0.302 | -6563.24 | 3264.74 | INCONCLUSIVE |
| orb_low_stop | 52 | 30.8 | -70.05 | -0.312 | 29 | 37.9 | -41.41 | -0.184 | -4843.57 | 3451.57 | INCONCLUSIVE |
| no_regime | 71 | 18.3 | -106.00 | -0.501 | 29 | 31.0 | -66.93 | -0.350 | -9466.74 | 4663.59 | INCONCLUSIVE |
| trail_plus_rs | 32 | 21.9 | -106.09 | -0.456 | 18 | 44.4 | -5.75 | -0.018 | -3498.27 | 2532.52 | INCONCLUSIVE |

## Ideas

- **baseline**: config.json as is: ORB + VWAP reclaim, 3R fixed target, Nifty green-day filter
- **target_2r**: closer 2R target (hit more often); min net R:R relaxed to 1.2 or nothing passes
- **breakeven_1r**: move the stop to entry once price reaches +1R
- **trail_1r**: after +1R, trail the stop 1R below the high; 3R target kept
- **let_run**: 5R target, trail 1R below the high after +1.5R: cut losers, let winners run to the close
- **rs_filter**: only stocks at least 0.5% stronger than the Nifty since the open
- **orb_only**: opening-range breakout alone
- **vwap_only**: VWAP reclaim alone
- **orb_30m**: 30-minute opening range instead of 15 (fewer, cleaner breakouts)
- **orb_low_stop**: stop at the range low instead of the midpoint (fewer whipsaws, smaller size)
- **no_regime**: drop the Nifty green-day filter
- **trail_plus_rs**: the two most plausible ideas a priori, together: trail_1r + rs_filter
