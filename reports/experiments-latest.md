# Experiments

Data 2026-08-04 to 2026-10-28 (59 sessions). In-sample before 2026-10-01, out-of-sample from it. All figures net of costs.
Pick on **in-sample** ₹/trade; read out-of-sample only as confirmation.

| variant | IS trades | IS win% | IS ₹/trade | IS avg R | OOS trades | OOS win% | OOS ₹/trade | OOS avg R | all net ₹ | charges ₹ |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 42 | 31.0 | -88.85 | -0.415 | 28 | 35.7 | -48.28 | -0.235 | -5083.77 | 3453.37 |
| target_2r | 7 | 42.9 | -74.19 | -0.326 | 13 | 15.4 | -104.11 | -0.437 | -1872.73 | 848.63 |
| breakeven_1r | 42 | 31.0 | -88.85 | -0.415 | 32 | 25.0 | -54.29 | -0.274 | -5469.24 | 3620.94 |
| trail_1r | 45 | 24.4 | -89.10 | -0.442 | 32 | 28.1 | -56.87 | -0.269 | -5829.09 | 3760.14 |
| let_run | 67 | 16.4 | -90.01 | -0.569 | 22 | 31.8 | -79.86 | -0.393 | -7787.59 | 4142.99 |
| rs_filter | 33 | 30.3 | -87.88 | -0.405 | 23 | 39.1 | -43.73 | -0.188 | -3905.92 | 2780.32 |
| orb_only | 42 | 31.0 | -88.85 | -0.415 | 27 | 37.0 | -53.26 | -0.259 | -5169.76 | 3427.06 |
| vwap_only | 9 | 11.1 | -161.99 | -0.701 | 17 | 29.4 | -32.62 | -0.152 | -2012.55 | 1362.00 |
| orb_30m | 45 | 17.8 | -109.88 | -0.543 | 29 | 24.1 | -75.33 | -0.425 | -7129.17 | 3351.12 |
| orb_low_stop | 50 | 32.0 | -69.32 | -0.306 | 30 | 33.3 | -62.42 | -0.284 | -5338.54 | 3387.44 |
| no_regime | 75 | 22.7 | -87.73 | -0.430 | 30 | 23.3 | -95.00 | -0.504 | -9429.39 | 4684.74 |
| trail_plus_rs | 33 | 24.2 | -93.52 | -0.429 | 23 | 34.8 | -51.52 | -0.227 | -4271.08 | 2778.63 |

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
