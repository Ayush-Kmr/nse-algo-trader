# Signal study

Every signal from 2026-08-06 to 2026-10-30, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-07. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 502 | -0.207 | -0.272 to -0.141 | -0.488 | square-off 163, stop 287, stop (gap) 3, target 48, target (gap) 1 |
| in-sample | 325 | -0.245 | -0.324 to -0.166 | -0.530 | square-off 98, stop 194, stop (gap) 2, target 31 |
| out-of-sample | 177 | -0.136 | -0.250 to -0.023 | -0.410 | square-off 65, stop 93, stop (gap) 1, target 17, target (gap) 1 |
| strategy: orb | 284 | -0.192 | -0.276 to -0.107 | -0.449 | square-off 122, stop 142, stop (gap) 2, target 17, target (gap) 1 |
| strategy: vwap_reclaim | 218 | -0.226 | -0.328 to -0.125 | -0.538 | square-off 41, stop 145, stop (gap) 1, target 31 |
| entry hour: 09 | 109 | -0.053 | -0.218 to +0.113 | -0.301 | square-off 40, stop 56, target 12, target (gap) 1 |
| entry hour: 10 | 206 | -0.251 | -0.352 to -0.149 | -0.546 | square-off 45, stop 137, stop (gap) 1, target 23 |
| entry hour: 11 | 95 | -0.191 | -0.341 to -0.041 | -0.475 | square-off 34, stop 49, stop (gap) 1, target 11 |
| entry hour: 12 | 53 | -0.376 | -0.518 to -0.235 | -0.665 | square-off 19, stop 32, stop (gap) 1, target 1 |
| entry hour: 13 | 14 | -0.209 | -0.575 to +0.157 | -0.494 | square-off 8, stop 5, target 1 |
| entry hour: 14 | 25 | -0.216 | -0.377 to -0.055 | -0.493 | square-off 17, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
