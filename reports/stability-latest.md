# Stability test

**Result: PASS**

Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **True** (79 and 79 trades).

| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean, saved and reloaded every tick | - | 4378 | 0 | 79 | 158 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 1 | 4178 | 200 | 76 | 152 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 2 | 4139 | 239 | 80 | 160 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 3 | 4147 | 231 | 78 | 156 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 4 | 4148 | 230 | 81 | 162 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 5 | 4170 | 208 | 79 | 158 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 1 | 3527 | 851 | 79 | 158 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 2 | 3530 | 850 | 79 | 157 | 0 | -1.03 | 2 | 3 | 0 | none |
| bad | 3 | 3480 | 899 | 77 | 154 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 4 | 3484 | 894 | 81 | 162 | 0 | -1.02 | 2 | 4 | 0 | none |
| bad | 5 | 3531 | 847 | 81 | 162 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 1 | 2298 | 2085 | 70 | 139 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 2 | 2262 | 2123 | 69 | 137 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 3 | 2274 | 2106 | 65 | 130 | 0 | -0.99 | 2 | 3 | 0 | none |
| severe | 4 | 2204 | 2179 | 68 | 136 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 5 | 2229 | 2152 | 65 | 129 | 0 | -1.00 | 2 | 3 | 0 | none |

This tests that the software holds up. It says nothing about whether the strategy makes money.
