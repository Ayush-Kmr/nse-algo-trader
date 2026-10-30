# Signal study

Every signal from 2026-08-06 to 2026-10-29, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-06. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 94 | -0.114 | -0.212 to -0.016 | -0.335 | square-off 83, stop 11 |
| in-sample | 43 | -0.149 | -0.312 to +0.014 | -0.365 | square-off 37, stop 6 |
| out-of-sample | 51 | -0.083 | -0.202 to +0.035 | -0.310 | square-off 46, stop 5 |
| strategy: afternoon_high | 94 | -0.114 | -0.212 to -0.016 | -0.335 | square-off 83, stop 11 |
| entry hour: 13 | 57 | -0.050 | -0.188 to +0.089 | -0.268 | square-off 52, stop 5 |
| entry hour: 14 | 37 | -0.212 | -0.336 to -0.088 | -0.439 | square-off 31, stop 6 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
