# Learned signal filter

1458 signals over 60 sessions, all strategies, no regime filter. Ridge regression on features known at the signal, fitted on earlier sessions only and scored on unseen ones.

**Verdict: INCONCLUSIVE: 1 out-of-sample trades, need 30+ before any conclusion.**

| unseen signals | count | avg gross R | 95% interval | avg net R |
|---|---|---|---|---|
| all | 866 | -0.183 | -0.232 to -0.134 | -0.460 |
| picked by the model | 1 | | | |

Signals on the same day move together, so these intervals are narrower than they should be.
