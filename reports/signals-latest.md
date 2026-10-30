# Signal study

Every signal from 2026-08-06 to 2026-10-29, with no position limits or risk blocks, sized as a fresh account.
Out-of-sample from 2026-10-06. R is planned risk. A real edge needs the gross interval above the cost of about 0.28R.

| slice | signals | avg gross R | 95% interval | avg net R | exits |
|---|---|---|---|---|---|
| all | 472 | -0.204 | -0.271 to -0.136 | -0.487 | square-off 151, stop 270, stop (gap) 3, target 47, target (gap) 1 |
| in-sample | 292 | -0.250 | -0.333 to -0.168 | -0.536 | square-off 90, stop 173, stop (gap) 2, target 27 |
| out-of-sample | 180 | -0.128 | -0.244 to -0.013 | -0.407 | square-off 61, stop 97, stop (gap) 1, target 20, target (gap) 1 |
| strategy: orb | 261 | -0.183 | -0.272 to -0.094 | -0.442 | square-off 112, stop 129, stop (gap) 2, target 17, target (gap) 1 |
| strategy: vwap_reclaim | 211 | -0.229 | -0.333 to -0.126 | -0.542 | square-off 39, stop 141, stop (gap) 1, target 30 |
| entry hour: 09 | 98 | -0.048 | -0.225 to +0.129 | -0.297 | square-off 34, stop 51, target 12, target (gap) 1 |
| entry hour: 10 | 196 | -0.241 | -0.345 to -0.136 | -0.537 | square-off 44, stop 129, stop (gap) 1, target 22 |
| entry hour: 11 | 90 | -0.199 | -0.355 to -0.042 | -0.485 | square-off 30, stop 48, stop (gap) 1, target 11 |
| entry hour: 12 | 51 | -0.361 | -0.507 to -0.216 | -0.651 | square-off 19, stop 30, stop (gap) 1, target 1 |
| entry hour: 13 | 13 | -0.164 | -0.548 to +0.219 | -0.453 | square-off 8, stop 4, target 1 |
| entry hour: 14 | 24 | -0.245 | -0.402 to -0.088 | -0.523 | square-off 16, stop 8 |

Hour rows were not pre-registered: read them as leads to retest, never as results.
