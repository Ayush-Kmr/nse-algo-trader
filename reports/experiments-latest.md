# Experiments

Data 2026-08-04 to 2026-10-29 (60 sessions). In-sample before 2026-10-05, out-of-sample from it. All figures net of costs.
Pick on **in-sample** ₹/trade; read out-of-sample only as confirmation.

Gate: 30+ out-of-sample trades and a lower bound on avg R above zero, corrected for 12 variants.

| variant | IS trades | IS win% | IS ₹/trade | IS avg R | OOS trades | OOS win% | OOS ₹/trade | OOS avg R | all net ₹ | charges ₹ | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 39 | 30.8 | -98.62 | -0.448 | 31 | 45.2 | -7.15 | -0.045 | -4067.81 | 3644.96 | FAILS |
| target_2r | 10 | 30.0 | -126.76 | -0.532 | 16 | 18.8 | -88.70 | -0.410 | -2686.71 | 1187.01 | INCONCLUSIVE |
| breakeven_1r | 40 | 30.0 | -95.91 | -0.444 | 31 | 29.0 | -31.28 | -0.156 | -4806.03 | 3651.13 | FAILS |
| trail_1r | 42 | 23.8 | -98.58 | -0.455 | 33 | 33.3 | -31.72 | -0.171 | -5187.10 | 3869.60 | FAILS |
| let_run | 61 | 14.8 | -97.74 | -0.527 | 19 | 31.6 | -35.05 | -0.180 | -6628.01 | 3895.16 | INCONCLUSIVE |
| rs_filter | 32 | 28.1 | -97.43 | -0.418 | 19 | 52.6 | +30.14 | +0.135 | -2545.19 | 2630.59 | INCONCLUSIVE |
| orb_only | 39 | 30.8 | -97.99 | -0.433 | 27 | 40.7 | -27.90 | -0.134 | -4574.94 | 3477.54 | INCONCLUSIVE |
| vwap_only | 10 | 0.0 | -213.25 | -0.908 | 14 | 42.9 | +5.60 | +0.029 | -2054.13 | 1304.33 | INCONCLUSIVE |
| orb_30m | 44 | 18.2 | -115.58 | -0.527 | 25 | 28.0 | -58.55 | -0.292 | -6549.41 | 3365.01 | INCONCLUSIVE |
| orb_low_stop | 52 | 30.8 | -67.57 | -0.300 | 29 | 37.9 | -37.66 | -0.170 | -4605.65 | 3514.30 | INCONCLUSIVE |
| no_regime | 72 | 20.8 | -99.16 | -0.460 | 28 | 32.1 | -67.12 | -0.344 | -9018.88 | 4816.98 | INCONCLUSIVE |
| trail_plus_rs | 32 | 21.9 | -103.34 | -0.442 | 19 | 47.4 | +18.18 | +0.084 | -2961.51 | 2613.91 | INCONCLUSIVE |

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
