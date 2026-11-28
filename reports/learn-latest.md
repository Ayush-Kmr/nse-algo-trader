# Learned signal filter

1597 signals over 60 sessions, all strategies, no regime filter. Ridge regression on features known at the signal, fitted on earlier sessions only and scored on unseen ones.

**Verdict: INCONCLUSIVE: 0 out-of-sample trades, need 30+ before any conclusion.**

| unseen signals | count | avg gross R | 95% interval | avg net R |
|---|---|---|---|---|
| all | 895 | -0.149 | -0.198 to -0.101 | -0.423 |
| picked by the model | 0 | | | |

Signals on the same day move together, so these intervals are narrower than they should be.
