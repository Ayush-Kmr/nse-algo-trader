# Strategy lab

Source: yahoo. 2026-08-05 to 2026-10-30 (60 sessions). Validation from 2026-09-25, test from 2026-10-14. ₹25,000 a trade, next-bar fills, all charges.

**No reliable trading edge was found.**

| strategy | side | stop, target (ATR) | train trades | train ₹/trade | val trades | val ₹/trade | val win % | val PF | val net ₹ | val max DD ₹ | test | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| opening-range breakout | long | 1.5, 3.0 | 360 | -59.79 | 262 | -98.89 | 32.4 | 0.43 | -25910 | 27060 | not reached | no |
| opening-range breakout | short | 1.0, 3.0 | 797 | -63.62 | 228 | -34.63 | 35.1 | 0.73 | -7897 | 14413 | not reached | no |
| VWAP continuation | long | 1.0, 2.0 | 2038 | -87.52 | 898 | -97.77 | 21.8 | 0.20 | -87798 | 87978 | not reached | no |
| VWAP continuation | short | 2.0, 3.0 | 3856 | -79.25 | 1140 | -48.32 | 39.6 | 0.56 | -55079 | 73087 | not reached | no |
| trend following | long | 1.0, 2.0 | 1839 | -81.58 | 811 | -100.37 | 20.8 | 0.18 | -81400 | 81466 | not reached | no |
| trend following | short | 2.0, 3.0 | 3438 | -77.95 | 860 | -12.08 | 49.0 | 0.86 | -10392 | 21949 | not reached | no |
| mean reversion | long | 1.0, 1.5 | 759 | -87.91 | 288 | -101.88 | 18.8 | 0.09 | -29342 | 29342 | not reached | no |
| mean reversion | short | 1.0, 1.5 | 535 | -87.13 | 144 | -73.65 | 32.6 | 0.22 | -10606 | 10606 | not reached | no |

## Monthly net ₹, validation

| strategy | side | months |
|---|---|---|
| opening-range breakout | long | 2026-09 -10003, 2026-10 -15907 |
| opening-range breakout | short | 2026-09 -8805, 2026-10 +908 |
| VWAP continuation | long | 2026-09 -26031, 2026-10 -61768 |
| VWAP continuation | short | 2026-09 -30004, 2026-10 -25075 |
| trend following | long | 2026-09 -27954, 2026-10 -53445 |
| trend following | short | 2026-09 -14483, 2026-10 +4091 |
| mean reversion | long | 2026-09 -7079, 2026-10 -22264 |
| mean reversion | short | 2026-09 -3525, 2026-10 -7080 |
