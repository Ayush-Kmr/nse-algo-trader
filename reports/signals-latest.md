# Signal study

Every signal from 2026-09-01 to 2026-11-27, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-11-02. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 688 | -0.183 | -0.241 to -0.125 | -0.459 | square-off 212, stop 394, stop (gap) 3, target 78, target (gap) 1 |
| in-sample | 446 | -0.210 | -0.279 to -0.140 | -0.490 | square-off 141, stop 256, stop (gap) 3, target 45, target (gap) 1 |
| out-of-sample | 242 | -0.134 | -0.239 to -0.028 | -0.403 | square-off 71, stop 138, target 33 |
| strategy: orb | 366 | -0.149 | -0.227 to -0.070 | -0.396 | square-off 162, stop 175, stop (gap) 2, target 26, target (gap) 1 |
| strategy: vwap_reclaim | 322 | -0.222 | -0.309 to -0.135 | -0.531 | square-off 50, stop 219, stop (gap) 1, target 52 |
| entry hour: 09 | 151 | -0.017 | -0.157 to +0.124 | -0.256 | square-off 62, stop 73, target 15, target (gap) 1 |
| entry hour: 10 | 301 | -0.230 | -0.319 to -0.140 | -0.521 | square-off 58, stop 201, stop (gap) 1, target 41 |
| entry hour: 11 | 122 | -0.238 | -0.368 to -0.108 | -0.521 | square-off 37, stop 69, stop (gap) 1, target 15 |
| entry hour: 12 | 59 | -0.304 | -0.475 to -0.133 | -0.587 | square-off 19, stop 35, stop (gap) 1, target 4 |
| entry hour: 13 | 26 | -0.074 | -0.345 to +0.197 | -0.356 | square-off 15, stop 8, target 3 |
| entry hour: 14 | 29 | -0.185 | -0.339 to -0.030 | -0.452 | square-off 21, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
