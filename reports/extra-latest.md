# Other intraday tests

₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.

## Finer timing, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| 5-minute range breakout | long | 7244 | -29.24 | -99.49 | -58.37 | -74.98 | no |
| 5-minute range breakdown | short | 8687 | -14.49 | -71.33 | -68.92 | -84.63 | no |
| 15-minute range breakout | long | 6553 | -25.23 | -92.16 | -61.73 | -78.26 | no |
| 15-minute range breakdown | short | 7713 | -8.23 | -74.13 | -41.66 | -57.86 | no |

## News proxy: big gaps on heavy volume

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| follow the gap | both | 910 | -30.58 | -73.71 | -114.43 | -162.83 | no |
| fade the gap | both | 910 | -15.65 | -64.99 | -86.18 | -134.78 | no |

## Pairs trading

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| same-industry pairs | both | 2153 | -26.62 | -88.29 | -100.32 | -107.29 | no |
