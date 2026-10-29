# Research log

Every idea tested, kept even when it fails. Results: `reports/experiments-latest.md`.
Run again with `python3 -m algo experiments` (add `--refresh` for new data).

## 2026-10-29 — round 1: 12 pre-registered variants, 59 sessions, 25 Nifty names

**Result: none has an edge. All 12 lose money in-sample, net of costs.** `config.json` is unchanged:
nothing earned a promotion.

| idea | in-sample ₹/trade | verdict |
|---|---|---|
| baseline (ORB + VWAP, 3R) | −88.85 | loses |
| closer 2R target | −74.19 (7 trades) | loses; most signals blocked by the net R:R rule |
| breakeven at +1R | −88.85 | no effect: trades rarely reach +1R |
| trail after +1R | −89.10 | no effect, same reason |
| let winners run (5R, trail) | −90.01 | worse |
| relative strength ≥ 0.5% vs Nifty | −87.88 | loses less only because it trades less |
| ORB alone | −88.85 | loses |
| VWAP reclaim alone | −161.99 (9 trades) | worst |
| 30-min opening range | −109.88 | worse |
| stop at range low | −69.32 | least bad, still loses |
| no Nifty filter | −87.73 | more trades, more total loss |
| trail + RS | −93.52 | loses |

### What the numbers say

1. **The breakouts do not follow through.** In-sample, 0 of 44 baseline trades reached the target;
   half hit the stop, half drifted to the 15:15 square-off. Exit tweaks (breakeven, trailing, bigger
   targets) cannot fix entries that do not move.
2. **There is no gross edge either.** Before charges the baseline is already negative
   (about −₹25 a trade). Charges (about ₹49 a trade, roughly 0.2R) then double the loss.
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
