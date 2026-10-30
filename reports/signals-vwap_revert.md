# Signal study

Every signal from 2026-08-07 to 2026-10-28, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-14. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 72 | -0.084 | -0.281 to +0.112 | -0.395 | square-off 16, stop 42, stop (gap) 1, target 13 |
| in-sample | 46 | -0.130 | -0.359 to +0.099 | -0.430 | square-off 11, stop 26, stop (gap) 1, target 8 |
| out-of-sample | 26 | -0.004 | -0.371 to +0.364 | -0.333 | square-off 5, stop 16, target 5 |
| strategy: vwap_revert | 72 | -0.084 | -0.281 to +0.112 | -0.395 | square-off 16, stop 42, stop (gap) 1, target 13 |
| entry hour: 10 | 4 | -0.366 | -1.018 to +0.285 | -0.654 | stop 3, target 1 |
| entry hour: 11 | 12 | -0.322 | -0.793 to +0.149 | -0.637 | square-off 1, stop 8, stop (gap) 1, target 2 |
| entry hour: 12 | 19 | +0.025 | -0.416 to +0.467 | -0.300 | square-off 3, stop 12, target 4 |
| entry hour: 13 | 20 | -0.173 | -0.542 to +0.195 | -0.475 | square-off 3, stop 13, target 4 |
| entry hour: 14 | 17 | +0.132 | -0.234 to +0.498 | -0.173 | square-off 9, stop 6, target 2 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
