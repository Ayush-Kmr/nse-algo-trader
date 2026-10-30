# Learned signal filter

1321 signals over 59 sessions, all strategies, no regime filter. Ridge regression on features known at the signal, fitted on earlier sessions only and scored on unseen ones.

**Verdict: INCONCLUSIVE: 2 out-of-sample trades, need 30+ before any conclusion.**

| unseen signals | count | avg gross R | 95% interval | avg net R |
|---|---|---|---|---|
| all | 783 | -0.199 | -0.251 to -0.148 | -0.482 |
| picked by the model | 2 | -0.539 | -0.917 to -0.160 | -0.691 |

Signals on the same day move together, so these intervals are narrower than they should be.
