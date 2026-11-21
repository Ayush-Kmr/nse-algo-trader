# Other intraday tests

₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.

## Finer timing, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| 5-minute range breakout | long | 7629 | +1.51 | -98.97 | +19.72 | +2.68 | no |
| 5-minute range breakdown | short | 8117 | -21.75 | -57.84 | -129.04 | -144.34 | no |
| 15-minute range breakout | long | 6939 | +1.08 | -94.77 | +10.30 | -6.58 | no |
| 15-minute range breakdown | short | 7139 | -10.79 | -49.60 | -112.52 | -128.00 | no |

## Groww guide rules, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| RSI divergence, buy | long | 2720 | -36.95 | -112.59 | -41.60 | -61.26 | no |
| RSI divergence, sell | short | 2068 | -64.05 | -88.18 | -162.51 | -181.23 | no |
| MACD divergence, buy | long | 3372 | -31.98 | -112.90 | -26.91 | -44.86 | no |
| MACD divergence, sell | short | 2640 | -60.60 | -84.84 | -163.62 | -180.56 | no |
| 3% gap up, range break | long | 24 | +0.00 | +0.00 | +0.00 | +0.00 | no |
| 3% gap down, range break | short | 21 | +0.00 | +0.00 | +0.00 | +0.00 | no |

## News proxy: big gaps on heavy volume

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| follow the gap | both | 938 | -30.71 | -74.44 | -112.26 | -160.46 | no |
| fade the gap | both | 938 | -12.53 | -62.30 | -81.58 | -127.28 | no |

## Pairs trading

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| same-industry pairs | both | 2282 | -28.68 | -88.82 | -103.41 | -110.51 | no |
