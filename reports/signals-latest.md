# Signal study

Every signal from 2026-08-18 to 2026-11-13, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-22. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 593 | -0.205 | -0.267 to -0.144 | -0.483 | square-off 182, stop 346, stop (gap) 3, target 61, target (gap) 1 |
| in-sample | 383 | -0.237 | -0.310 to -0.164 | -0.519 | square-off 117, stop 225, stop (gap) 2, target 39 |
| out-of-sample | 210 | -0.148 | -0.259 to -0.037 | -0.419 | square-off 65, stop 121, stop (gap) 1, target 22, target (gap) 1 |
| strategy: orb | 329 | -0.166 | -0.248 to -0.084 | -0.419 | square-off 141, stop 162, stop (gap) 2, target 23, target (gap) 1 |
| strategy: vwap_reclaim | 264 | -0.254 | -0.347 to -0.161 | -0.563 | square-off 41, stop 184, stop (gap) 1, target 38 |
| entry hour: 09 | 142 | -0.039 | -0.186 to +0.107 | -0.284 | square-off 53, stop 73, target 15, target (gap) 1 |
| entry hour: 10 | 252 | -0.265 | -0.358 to -0.173 | -0.560 | square-off 49, stop 172, stop (gap) 1, target 30 |
| entry hour: 11 | 103 | -0.234 | -0.370 to -0.097 | -0.517 | square-off 36, stop 55, stop (gap) 1, target 11 |
| entry hour: 12 | 55 | -0.297 | -0.480 to -0.115 | -0.581 | square-off 17, stop 33, stop (gap) 1, target 4 |
| entry hour: 13 | 14 | -0.223 | -0.586 to +0.139 | -0.496 | square-off 8, stop 5, target 1 |
| entry hour: 14 | 27 | -0.214 | -0.363 to -0.065 | -0.487 | square-off 19, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
