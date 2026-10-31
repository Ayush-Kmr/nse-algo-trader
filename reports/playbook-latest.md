# Day-trader-skill rules on NSE

Rules copied unchanged from the repo. ₹25,000 a trade, flat by 15:15, 0.06% a fill, Indian charges. A pass needs 100+ trades, a day-clustered lower bound above zero, and both halves positive.

**Nothing passed.**

## Opening-range breakout, midpoint stop

200 stocks, 2026-08-05 to 2026-10-30, Yahoo 5-minute bars.

| version | trades | win % | avg R before costs | gross ₹/trade | net ₹/trade | net ₹ | PF | max DD ₹ | lower bound | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| 1R target, next bar's open | 6439 | 38.1 | -0.032 | -32.65 | -88.71 | -571220 | 0.27 | 571535 | -99.80 | no |
| 1R target, signal bar's close (repo's history) | 6439 | 38.4 | -0.036 | -33.39 | -89.45 | -575971 | 0.27 | 576377 | -100.46 | no |
| 2R target, next bar's open | 6439 | 31.1 | -0.012 | -28.90 | -84.97 | -547096 | 0.40 | 547930 | -99.29 | no |
| 2R target, signal bar's close (repo's history) | 6439 | 31.1 | -0.015 | -29.08 | -85.14 | -548211 | 0.40 | 549061 | -99.76 | no |

## Daily scanner setups, next day open to close

200 of today's stocks, 2006-12-12 to 2026-10-30, Yahoo daily bars. Survivorship flatters these.

| setup | trades | win % | gross ₹/trade | net ₹/trade | early half | late half | lower bound | pass |
|---|---|---|---|---|---|---|---|---|
| breakout_20d | 100353 | 36.5 | -56.26 | -112.33 | -101.80 | -122.86 | -126.78 | no |
| bull_flag | 36834 | 38.1 | -49.30 | -105.37 | -95.90 | -114.85 | -123.26 | no |
| reclaim_ma20 | 44456 | 37.8 | -42.44 | -98.51 | -92.77 | -104.25 | -112.80 | no |
| oversold | 30355 | 40.6 | -55.82 | -111.89 | -151.97 | -71.96 | -172.17 | no |
| oversold_bounce | 15411 | 40.7 | -36.93 | -93.00 | -91.39 | -94.61 | -152.28 | no |
| every stock, every day | 772328 | 37.4 | -54.73 | -110.80 | -111.52 | -110.07 | -120.66 | no |

## The full pipeline: yesterday's setup, then today's breakout (2R, next open)

| setup | trades | win % | gross ₹/trade | net ₹/trade | net ₹ |
|---|---|---|---|---|---|
| breakout_20d | 337 | 25.5 | -44.91 | -100.97 | -34027 |
| bull_flag | 139 | 28.8 | -34.05 | -90.11 | -12526 |
| reclaim_ma20 | 338 | 29.3 | -28.24 | -84.30 | -28495 |
| oversold | 512 | 37.7 | +4.46 | -51.61 | -26426 |
| oversold_bounce | 264 | 34.5 | -21.86 | -77.92 | -20571 |

## Time Machine odds against what happened (1R trades)

Odds use 200 replays from earlier days of the same stock, seed 19.

| its odds of target first | trades | average odds % | actual target first % | net ₹/trade |
|---|---|---|---|---|
| under 45% | 1525 | 39.0 | 52.7 | -81.16 |
| 45% to 55% | 1970 | 49.6 | 49.2 | -87.91 |
| 55% and over | 929 | 61.1 | 50.3 | -86.90 |
