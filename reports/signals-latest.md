# Signal study

Every signal from 2026-08-14 to 2026-11-06, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-15. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 551 | -0.187 | -0.251 to -0.122 | -0.466 | square-off 175, stop 314, stop (gap) 3, target 58, target (gap) 1 |
| in-sample | 338 | -0.235 | -0.314 to -0.157 | -0.520 | square-off 101, stop 201, stop (gap) 2, target 34 |
| out-of-sample | 213 | -0.109 | -0.218 to -0.000 | -0.380 | square-off 74, stop 113, stop (gap) 1, target 24, target (gap) 1 |
| strategy: orb | 303 | -0.146 | -0.232 to -0.061 | -0.400 | square-off 134, stop 144, stop (gap) 2, target 22, target (gap) 1 |
| strategy: vwap_reclaim | 248 | -0.236 | -0.333 to -0.139 | -0.546 | square-off 41, stop 170, stop (gap) 1, target 36 |
| entry hour: 09 | 123 | -0.007 | -0.167 to +0.153 | -0.252 | square-off 46, stop 62, target 14, target (gap) 1 |
| entry hour: 10 | 228 | -0.242 | -0.341 to -0.143 | -0.537 | square-off 46, stop 153, stop (gap) 1, target 28 |
| entry hour: 11 | 105 | -0.238 | -0.373 to -0.103 | -0.524 | square-off 36, stop 57, stop (gap) 1, target 11 |
| entry hour: 12 | 51 | -0.265 | -0.459 to -0.071 | -0.547 | square-off 17, stop 29, stop (gap) 1, target 4 |
| entry hour: 13 | 17 | -0.150 | -0.462 to +0.161 | -0.423 | square-off 11, stop 5, target 1 |
| entry hour: 14 | 27 | -0.214 | -0.363 to -0.065 | -0.487 | square-off 19, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
