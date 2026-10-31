# Signal study

Every signal from 2026-08-06 to 2026-10-30, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-07. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 493 | -0.201 | -0.267 to -0.135 | -0.483 | square-off 159, stop 281, stop (gap) 3, target 49, target (gap) 1 |
| in-sample | 318 | -0.241 | -0.321 to -0.160 | -0.527 | square-off 94, stop 190, stop (gap) 2, target 32 |
| out-of-sample | 175 | -0.129 | -0.244 to -0.014 | -0.403 | square-off 65, stop 91, stop (gap) 1, target 17, target (gap) 1 |
| strategy: orb | 274 | -0.188 | -0.275 to -0.102 | -0.446 | square-off 118, stop 136, stop (gap) 2, target 17, target (gap) 1 |
| strategy: vwap_reclaim | 219 | -0.217 | -0.320 to -0.114 | -0.529 | square-off 41, stop 145, stop (gap) 1, target 32 |
| entry hour: 09 | 103 | -0.057 | -0.229 to +0.115 | -0.306 | square-off 36, stop 54, target 12, target (gap) 1 |
| entry hour: 10 | 202 | -0.239 | -0.342 to -0.135 | -0.535 | square-off 45, stop 133, stop (gap) 1, target 23 |
| entry hour: 11 | 97 | -0.201 | -0.348 to -0.054 | -0.486 | square-off 34, stop 51, stop (gap) 1, target 11 |
| entry hour: 12 | 51 | -0.364 | -0.511 to -0.218 | -0.651 | square-off 19, stop 30, stop (gap) 1, target 1 |
| entry hour: 13 | 15 | -0.104 | -0.502 to +0.294 | -0.391 | square-off 8, stop 5, target 2 |
| entry hour: 14 | 25 | -0.216 | -0.377 to -0.055 | -0.493 | square-off 17, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
