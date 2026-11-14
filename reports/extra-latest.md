# Other intraday tests

₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.

## Finer timing, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| 5-minute range breakout | long | 7512 | -9.00 | -99.51 | -4.77 | -22.18 | no |
| 5-minute range breakdown | short | 8282 | -19.38 | -61.08 | -109.71 | -125.30 | no |
| 15-minute range breakout | long | 6828 | -9.55 | -95.65 | -14.49 | -31.74 | no |
| 15-minute range breakdown | short | 7333 | -11.05 | -57.92 | -90.07 | -106.42 | no |

## Groww guide rules, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| RSI divergence, buy | long | 2720 | -38.68 | -112.51 | -56.02 | -74.59 | no |
| RSI divergence, sell | short | 1979 | -56.44 | -85.82 | -155.52 | -176.16 | no |
| MACD divergence, buy | long | 3429 | -33.77 | -111.79 | -43.08 | -60.08 | no |
| MACD divergence, sell | short | 2583 | -51.52 | -85.28 | -140.55 | -160.45 | no |
| 3% gap up, range break | long | 25 | +0.00 | +0.00 | +0.00 | +0.00 | no |
| 3% gap down, range break | short | 20 | +0.00 | +0.00 | +0.00 | +0.00 | no |

## News proxy: big gaps on heavy volume

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| follow the gap | both | 936 | -29.29 | -75.39 | -106.49 | -155.50 | no |
| fade the gap | both | 936 | -14.90 | -63.90 | -85.95 | -132.13 | no |

## Pairs trading

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| same-industry pairs | both | 2261 | -28.05 | -88.75 | -102.00 | -109.10 | no |
