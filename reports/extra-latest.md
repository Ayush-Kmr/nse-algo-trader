# Other intraday tests

₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.

## Finer timing, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| 5-minute range breakout | long | 7580 | -2.19 | -86.42 | -8.53 | -25.80 | no |
| 5-minute range breakdown | short | 8135 | -15.66 | -62.33 | -94.46 | -109.39 | no |
| 15-minute range breakout | long | 6923 | -3.36 | -83.09 | -17.67 | -34.76 | no |
| 15-minute range breakdown | short | 7159 | -6.84 | -51.14 | -91.01 | -105.55 | no |

## Groww guide rules, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| RSI divergence, buy | long | 2766 | -40.61 | -104.00 | -80.86 | -97.48 | no |
| RSI divergence, sell | short | 2053 | -56.69 | -89.18 | -151.01 | -171.55 | no |
| MACD divergence, buy | long | 3410 | -38.26 | -101.75 | -78.16 | -94.41 | no |
| MACD divergence, sell | short | 2625 | -55.05 | -86.38 | -156.24 | -174.53 | no |
| 3% gap up, range break | long | 26 | +0.00 | +0.00 | +0.00 | +0.00 | no |
| 3% gap down, range break | short | 22 | +0.00 | +0.00 | +0.00 | +0.00 | no |

## News proxy: big gaps on heavy volume

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| follow the gap | both | 938 | -29.71 | -74.22 | -109.29 | -158.51 | no |
| fade the gap | both | 938 | -12.74 | -62.45 | -81.73 | -127.59 | no |

## Pairs trading

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| same-industry pairs | both | 2303 | -28.53 | -91.87 | -100.32 | -107.50 | no |
