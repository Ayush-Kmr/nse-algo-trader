# Stability test

**Result: PASS**

Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **True** (88 and 88 trades).

| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean, saved and reloaded every tick | - | 4378 | 0 | 88 | 176 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 1 | 4152 | 226 | 88 | 176 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 2 | 4139 | 239 | 88 | 176 | 0 | -1.01 | 2 | 3 | 0 | none |
| mild | 3 | 4147 | 231 | 89 | 178 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 4 | 4148 | 230 | 88 | 176 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 5 | 4170 | 208 | 91 | 182 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 1 | 3529 | 851 | 86 | 172 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 2 | 3529 | 849 | 82 | 164 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 3 | 3479 | 899 | 85 | 170 | 0 | -1.02 | 2 | 4 | 0 | none |
| bad | 4 | 3484 | 894 | 87 | 174 | 0 | -1.02 | 2 | 3 | 0 | none |
| bad | 5 | 3531 | 847 | 88 | 176 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 1 | 2267 | 2115 | 77 | 154 | 0 | -0.99 | 2 | 3 | 0 | none |
| severe | 2 | 2259 | 2121 | 82 | 164 | 0 | -0.99 | 2 | 3 | 0 | none |
| severe | 3 | 2259 | 2119 | 74 | 148 | 0 | -1.02 | 2 | 3 | 0 | none |
| severe | 4 | 2193 | 2187 | 72 | 144 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 5 | 2240 | 2138 | 77 | 154 | 0 | -1.01 | 2 | 3 | 0 | none |

This tests that the software holds up. It says nothing about whether the strategy makes money.
