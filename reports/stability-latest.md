# Stability test

**Result: PASS**

Every tick reloads state from JSON, as a real run does. Clean replay matches the backtest: **True** (66 and 66 trades).

| run | seed | ticks run | ticks lost | trades | charts | chart errors | worst day % | max open | max entries | left open | rule breaches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| clean, saved and reloaded every tick | - | 4305 | 0 | 66 | 132 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 1 | 4110 | 195 | 67 | 134 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 2 | 4072 | 233 | 65 | 130 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 3 | 4089 | 216 | 66 | 132 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 4 | 4078 | 227 | 67 | 134 | 0 | -1.02 | 2 | 3 | 0 | none |
| mild | 5 | 4100 | 205 | 64 | 128 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 1 | 3462 | 843 | 64 | 128 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 2 | 3473 | 834 | 69 | 138 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 3 | 3425 | 881 | 66 | 132 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 4 | 3426 | 879 | 67 | 134 | 0 | -1.01 | 2 | 3 | 0 | none |
| bad | 5 | 3479 | 826 | 67 | 134 | 0 | -1.02 | 2 | 4 | 0 | none |
| severe | 1 | 2228 | 2084 | 52 | 103 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 2 | 2267 | 2043 | 53 | 105 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 3 | 2266 | 2043 | 46 | 90 | 0 | -0.97 | 2 | 2 | 0 | none |
| severe | 4 | 2178 | 2129 | 52 | 104 | 0 | -1.01 | 2 | 3 | 0 | none |
| severe | 5 | 2247 | 2064 | 56 | 112 | 0 | -1.02 | 2 | 3 | 0 | none |

This tests that the software holds up. It says nothing about whether the strategy makes money.
