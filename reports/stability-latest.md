# Stability test

**Result: PASS**

Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **True** (74 and 74 trades).

| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean, saved and reloaded every tick | - | 4378 | 0 | 74 | 148 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 1 | 4179 | 200 | 76 | 152 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 2 | 4139 | 239 | 76 | 152 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 3 | 4147 | 231 | 75 | 150 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 4 | 4148 | 230 | 75 | 150 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 5 | 4170 | 208 | 78 | 156 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 1 | 3527 | 851 | 72 | 144 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 2 | 3529 | 849 | 80 | 160 | 0 | -1.01 | 2 | 4 | 0 | none |
| bad | 3 | 3479 | 899 | 76 | 152 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 4 | 3484 | 894 | 71 | 142 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 5 | 3532 | 847 | 74 | 148 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 1 | 2296 | 2083 | 66 | 132 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 2 | 2305 | 2077 | 63 | 126 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 3 | 2260 | 2120 | 59 | 118 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 4 | 2194 | 2187 | 71 | 142 | 0 | -1.01 | 2 | 4 | 0 | none |
| severe | 5 | 2232 | 2148 | 58 | 116 | 0 | -1.01 | 2 | 3 | 0 | none |

This tests that the software holds up. It says nothing about whether the strategy makes money.
