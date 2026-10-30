# Research log

Every idea tested, kept even when it fails. Results: `reports/experiments-latest.md`.
Run again with `python3 -m algo experiments` (add `--refresh` for new data).

## 2026-10-30 — round 1 rerun after the bug fixes

Corrected charges (₹5 minimum brokerage, exchange 0.0030699%), the ₹5,000 minimum position, the
stricter cost check, and one more session (60, so out-of-sample now starts 2026-10-05). The table
below keeps the original 2026-10-29 numbers; current ones are in `reports/experiments-latest.md`.

**Still nothing passes, and all 12 still lose in-sample.** Baseline: 70 trades, net −₹4,068, gross
−₹423, charges ₹3,645. Out-of-sample it is −₹7.15 a trade on 31 trades, so it fails. `rs_filter`
is positive out-of-sample (+₹30.14 a trade) but on only 19 trades after losing in-sample, so it is
a lead to retest on more data. Do not promote it. Most of the shift from 2026-10-29 comes from the
moved split and the added session, so do not read it as an improvement.

## 2026-10-29 — round 1: 12 pre-registered variants, 59 sessions, 25 Nifty names

**Result: none has an edge. All 12 lose money in-sample, net of costs.** `config.json` is unchanged:
nothing earned a promotion.

| idea | in-sample ₹/trade | verdict |
|---|---|---|
| baseline (ORB + VWAP, 3R) | −88.85 | loses |
| closer 2R target | −74.19 (7 trades) | loses; most signals blocked by the net R:R rule |
| breakeven at +1R | −88.85 | no in-sample change: trades that reached +1R did not fall back to entry |
| trail after +1R | −89.10 | fewer wins: exits trades that were holding their gains |
| let winners run (5R, trail) | −90.01 | worse |
| relative strength ≥ 0.5% vs Nifty | −87.88 | loses less only because it trades less |
| ORB alone | −88.85 | loses |
| VWAP reclaim alone | −161.99 (9 trades) | worst |
| 30-min opening range | −109.88 | worse |
| stop at range low | −69.32 | least bad, still loses |
| no Nifty filter | −87.73 | more trades, more total loss |
| trail + RS | −93.52 | loses |

### What the numbers say

1. **The 3R target is almost never reached.** Only 1 of 71 trades hit it (first backtest report);
   32 hit the stop and 38 went to the 15:15 square-off. The square-offs averaged +0.35R gross, so
   the trades that survive do make money: they just do not travel 3R. *Corrected 2026-10-30: this
   said trades rarely reach +1R and exit changes cannot help. `trail_1r` shares the +1R trigger and
   changed in-sample results, so trades do reach +1R. Time or volatility exits are still untested.*
2. **The gross result is not distinguishable from zero.** Gross was about −₹24 a trade, or −0.13R
   with a standard error of 0.09R. Charges (about ₹49 a trade, roughly 0.23R) make the net result
   clearly negative: −0.36R, 95% CI −0.53R to −0.20R. *Corrected 2026-10-30: this said there was
   no gross edge, which 71 trades cannot show either way.*
3. **Costs set a high bar.** At ₹50k and 0.5% risk, a trade must make about 0.2R just to pay charges.
   An idea has to show clearly positive *gross* results before it is worth testing net.

### Caveats

59 sessions is a short window (Yahoo keeps 60 days of 5-minute bars). Out-of-sample has under
30 trades for every variant, so no out-of-sample number here means much on its own.

### What to try next (not yet tested)

- Different entries rather than different exits: e.g. a pullback after a strong open, gap-and-go
  on stocks with news, or mean reversion back to VWAP after an extended move.
- A longer history source (SmartAPI candles, years of 5-minute data) so results mean something.
- Fewer, larger trades so the flat brokerage weighs less, which only helps if the per-trade edge is real.
