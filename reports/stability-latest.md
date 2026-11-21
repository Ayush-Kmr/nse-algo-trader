# Stability test

**Result: PASS**

Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **True** (85 and 85 trades).

| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean, saved and reloaded every tick | - | 4378 | 0 | 85 | 170 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 1 | 4178 | 200 | 86 | 172 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 2 | 4139 | 239 | 87 | 174 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 3 | 4147 | 231 | 86 | 172 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 4 | 4148 | 230 | 83 | 166 | 0 | -1.01 | 2 | 2 | 0 | none |
| mild | 5 | 4170 | 208 | 86 | 172 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 1 | 3528 | 851 | 85 | 170 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 2 | 3530 | 850 | 86 | 172 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 3 | 3479 | 899 | 86 | 172 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 4 | 3509 | 870 | 90 | 180 | 0 | -1.01 | 2 | 4 | 0 | none |
| bad | 5 | 3532 | 847 | 82 | 164 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 1 | 2267 | 2115 | 73 | 146 | 0 | -1.02 | 2 | 4 | 0 | none |
| severe | 2 | 2306 | 2078 | 68 | 135 | 0 | -1.00 | 2 | 3 | 0 | none |
| severe | 3 | 2274 | 2106 | 72 | 144 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 4 | 2194 | 2187 | 73 | 145 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 5 | 2231 | 2148 | 70 | 140 | 0 | -0.94 | 2 | 3 | 0 | none |

This tests that the software holds up. It says nothing about whether the strategy makes money.
