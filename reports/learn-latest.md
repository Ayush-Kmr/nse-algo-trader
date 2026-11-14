# Learned signal filter

1479 signals over 60 sessions, all strategies, no regime filter. Ridge regression on features known at the signal, fitted on earlier sessions only and scored on unseen ones.

**Verdict: INCONCLUSIVE: 0 out-of-sample trades, need 30+ before any conclusion.**

| unseen signals | count | avg gross R | 95% interval | avg net R |
|---|---|---|---|---|
| all | 887 | -0.187 | -0.235 to -0.139 | -0.463 |
| picked by the model | 0 | | | |

Signals on the same day move together, so these intervals are narrower than they should be.
