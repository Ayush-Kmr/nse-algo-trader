# Learned signal filter

1336 signals over 60 sessions, all strategies, no regime filter. Ridge regression on features known at the signal, fitted on earlier sessions only and scored on unseen ones.

**Verdict: INCONCLUSIVE: 4 out-of-sample trades, need 30+ before any conclusion.**

| unseen signals | count | avg gross R | 95% interval | avg net R |
|---|---|---|---|---|
| all | 810 | -0.204 | -0.254 to -0.154 | -0.487 |
| picked by the model | 4 | -0.331 | -0.612 to -0.049 | -0.464 |

Signals on the same day move together, so these intervals are narrower than they should be.
