# Stability test

**Result: PASS**

Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **True** (69 and 69 trades).

| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean, saved and reloaded every tick | - | 4378 | 0 | 69 | 138 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 1 | 4178 | 200 | 69 | 138 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 2 | 4139 | 239 | 68 | 136 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 3 | 4160 | 218 | 69 | 138 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 4 | 4148 | 230 | 70 | 140 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 5 | 4170 | 208 | 68 | 136 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 1 | 3527 | 851 | 68 | 136 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 2 | 3530 | 850 | 72 | 144 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 3 | 3480 | 899 | 68 | 136 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 4 | 3484 | 894 | 71 | 142 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 5 | 3531 | 847 | 68 | 136 | 0 | -1.02 | 2 | 4 | 0 | none |
| severe | 1 | 2278 | 2105 | 57 | 113 | 0 | -1.02 | 2 | 4 | 0 | none |
| severe | 2 | 2306 | 2077 | 55 | 109 | 0 | -1.00 | 2 | 3 | 0 | none |
| severe | 3 | 2307 | 2078 | 51 | 99 | 0 | -0.99 | 2 | 2 | 0 | none |
| severe | 4 | 2203 | 2177 | 52 | 103 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 5 | 2228 | 2153 | 59 | 118 | 0 | -1.01 | 2 | 3 | 0 | none |

This tests that the software holds up. It says nothing about whether the strategy makes money.
