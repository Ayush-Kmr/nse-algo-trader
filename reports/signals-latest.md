# Signal study

Every signal from 2026-08-25 to 2026-11-20, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-28. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 647 | -0.167 | -0.227 to -0.106 | -0.445 | square-off 208, stop 361, stop (gap) 3, target 74, target (gap) 1 |
| in-sample | 409 | -0.232 | -0.303 to -0.161 | -0.515 | square-off 124, stop 240, stop (gap) 3, target 41, target (gap) 1 |
| out-of-sample | 238 | -0.054 | -0.161 to +0.053 | -0.326 | square-off 84, stop 121, target 33 |
| strategy: orb | 349 | -0.129 | -0.209 to -0.048 | -0.380 | square-off 159, stop 161, stop (gap) 2, target 26, target (gap) 1 |
| strategy: vwap_reclaim | 298 | -0.211 | -0.301 to -0.121 | -0.521 | square-off 49, stop 200, stop (gap) 1, target 48 |
| entry hour: 09 | 149 | -0.023 | -0.166 to +0.120 | -0.266 | square-off 59, stop 74, target 15, target (gap) 1 |
| entry hour: 10 | 275 | -0.213 | -0.306 to -0.120 | -0.508 | square-off 57, stop 179, stop (gap) 1, target 38 |
| entry hour: 11 | 114 | -0.196 | -0.332 to -0.060 | -0.484 | square-off 37, stop 61, stop (gap) 1, target 15 |
| entry hour: 12 | 55 | -0.277 | -0.458 to -0.095 | -0.556 | square-off 19, stop 31, stop (gap) 1, target 4 |
| entry hour: 13 | 25 | -0.127 | -0.372 to +0.118 | -0.409 | square-off 15, stop 8, target 2 |
| entry hour: 14 | 29 | -0.173 | -0.329 to -0.018 | -0.441 | square-off 21, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
