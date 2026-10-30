# Other intraday tests

₹25,000 a trade, same charges and slippage, out by the close. A pass needs a positive early period and a corrected lower bound above zero on the late one.

## Finer timing, 5-minute bars

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| 5-minute range breakout | long | 7244 | -30.70 | -100.92 | -59.89 | -76.45 | no |
| 5-minute range breakdown | short | 8687 | -13.21 | -69.86 | -68.04 | -83.74 | no |
| 15-minute range breakout | long | 6553 | -26.82 | -93.72 | -63.37 | -79.84 | no |
| 15-minute range breakdown | short | 7714 | -7.07 | -72.80 | -40.86 | -57.05 | no |

## News proxy: big gaps on heavy volume

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| follow the gap | both | 925 | -31.32 | -74.44 | -114.89 | -162.48 | no |
| fade the gap | both | 925 | -14.35 | -62.74 | -86.72 | -134.40 | no |

## Pairs trading

| test | side | trades | gross ₹/trade | early net ₹ | late net ₹ | late lower bound | pass |
|---|---|---|---|---|---|---|---|
| same-industry pairs | both | 2155 | -27.16 | -88.29 | -101.36 | -108.34 | no |
