# Signal study

Every signal from 2026-08-06 to 2026-10-29, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-06. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 487 | -0.210 | -0.276 to -0.144 | -0.492 | square-off 156, stop 280, stop (gap) 3, target 47, target (gap) 1 |
| in-sample | 303 | -0.251 | -0.331 to -0.170 | -0.535 | square-off 95, stop 179, stop (gap) 2, target 27 |
| out-of-sample | 184 | -0.143 | -0.257 to -0.029 | -0.420 | square-off 61, stop 101, stop (gap) 1, target 20, target (gap) 1 |
| strategy: orb | 272 | -0.189 | -0.277 to -0.102 | -0.448 | square-off 116, stop 136, stop (gap) 2, target 17, target (gap) 1 |
| strategy: vwap_reclaim | 215 | -0.236 | -0.337 to -0.134 | -0.548 | square-off 40, stop 144, stop (gap) 1, target 30 |
| entry hour: 09 | 104 | -0.044 | -0.214 to +0.126 | -0.293 | square-off 38, stop 53, target 12, target (gap) 1 |
| entry hour: 10 | 205 | -0.259 | -0.360 to -0.159 | -0.555 | square-off 45, stop 137, stop (gap) 1, target 22 |
| entry hour: 11 | 89 | -0.194 | -0.352 to -0.036 | -0.479 | square-off 30, stop 47, stop (gap) 1, target 11 |
| entry hour: 12 | 52 | -0.369 | -0.512 to -0.225 | -0.658 | square-off 19, stop 31, stop (gap) 1, target 1 |
| entry hour: 13 | 13 | -0.164 | -0.548 to +0.219 | -0.453 | square-off 8, stop 4, target 1 |
| entry hour: 14 | 24 | -0.245 | -0.402 to -0.088 | -0.523 | square-off 16, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
