# Other intraday tests

₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.

## Finer timing, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| 5-minute range breakout | long | 7415 | -6.90 | -102.72 | +5.13 | -11.82 | no |
| 5-minute range breakdown | short | 8391 | -20.82 | -58.75 | -121.31 | -137.23 | no |
| 15-minute range breakout | long | 6719 | -5.33 | -96.98 | -2.68 | -19.39 | no |
| 15-minute range breakdown | short | 7421 | -13.00 | -60.81 | -91.43 | -108.52 | no |

## Groww guide rules, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| RSI divergence, buy | long | 2612 | -38.60 | -115.02 | -44.65 | -65.21 | no |
| RSI divergence, sell | short | 2050 | -62.61 | -93.17 | -159.28 | -178.70 | no |
| MACD divergence, buy | long | 3370 | -36.33 | -114.15 | -41.25 | -59.49 | no |
| MACD divergence, sell | short | 2605 | -53.02 | -86.09 | -139.74 | -158.30 | no |
| 3% gap up, range break | long | 22 | +0.00 | +0.00 | +0.00 | +0.00 | no |
| 3% gap down, range break | short | 22 | +0.00 | +0.00 | +0.00 | +0.00 | no |

## News proxy: big gaps on heavy volume

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| follow the gap | both | 929 | -28.75 | -73.54 | -107.77 | -155.85 | no |
| fade the gap | both | 929 | -15.85 | -63.18 | -89.70 | -134.85 | no |

## Pairs trading

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| same-industry pairs | both | 2194 | -25.60 | -85.27 | -100.31 | -107.31 | no |
