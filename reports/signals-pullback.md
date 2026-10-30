# Signal study

Every signal from 2026-08-06 to 2026-10-29, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-09. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 139 | -0.231 | -0.350 to -0.112 | -0.539 | square-off 10, stop 92, target 37 |
| in-sample | 77 | -0.200 | -0.363 to -0.038 | -0.512 | square-off 4, stop 50, target 23 |
| out-of-sample | 62 | -0.268 | -0.444 to -0.093 | -0.572 | square-off 6, stop 42, target 14 |
| strategy: pullback | 139 | -0.231 | -0.350 to -0.112 | -0.539 | square-off 10, stop 92, target 37 |
| entry hour: 10 | 99 | -0.191 | -0.340 to -0.043 | -0.503 | square-off 3, stop 67, target 29 |
| entry hour: 11 | 27 | -0.253 | -0.519 to +0.013 | -0.563 | square-off 1, stop 18, target 8 |
| entry hour: 12 | 7 | -0.509 | -0.804 to -0.215 | -0.787 | square-off 2, stop 5 |
| entry hour: 13 | 4 | -0.446 | -0.673 to -0.220 | -0.705 | square-off 3, stop 1 |
| entry hour: 14 | 2 | -0.465 | -0.846 to -0.085 | -0.781 | square-off 1, stop 1 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
