# Research log

Every idea tested, kept even when it fails. Results: `reports/experiments-latest.md`.
Run again with `python3 -m algo experiments` (add `--refresh` for new data).

## 2026-10-31 — delivery, finer timing, news proxy and pairs

`python3 -m algo delivery` and `python3 -m algo extra`. Reports: `reports/delivery-latest.md`,
`reports/extra-latest.md`. Rules fixed in the code before the first run.

**Intraday and pairs: all failed.** 5-minute and 15-minute range breaks, long and short: about −₹41 to
−₹68 a trade late in the sample. Big gaps on heavy volume, used as a stand-in for news: −₹87 to
−₹115. Same-industry pairs, 2,155 trades: −₹101.

**Delivery: 12-1 momentum passed, with a serious caveat.** Jan 2009 to Sep 2026, ₹50,000, 10 stocks,
monthly, real delivery charges, no dividends or tax: +40.9% a year, against +24.4% for an equal-weight
hold of the same stocks and +13.2% for the Nifty ETF. The other five strategies failed.

The stocks are today's Nifty 200, which already knows who survived and grew. That bias helps
momentum more than most strategies, so +40.9% is not a realistic estimate.

**Rerun with less hindsight: momentum no longer passes.** No free dated Nifty 200 membership exists,
and Yahoo has no prices for delisted companies, so an exact point-in-time test is not possible. Instead,
each month used the 200 most-traded stocks at that time, from today's Nifty 500. Momentum made +28.8% a
year against +19.9% for equal-weight and +13.2% for the Nifty ETF, with a 39% worst fall. It led in both
halves, but the corrected lower bound was −3.8% a year, so **it fails**. Failed companies are still
missing, so even this is flattered.

Real-world check on the same idea: Nifty200 Momentum 30 TRI, about 18.8% a year since April 2005 against
13.9% for Nifty 200 TRI (HDFC material, June 2026; the early years are likely back-calculated). The
tradable ETF `MOMENTUM.NS` went from 19.4 to 29.0 between Sep 2022 and Oct 2026, about 10% a year,
against about 8.5% for `NIFTYBEES`, price only. That is a real but modest edge, and far below +40.9%.

Not tested: options and order-book strategies, which have no honest free history.

## 2026-10-31 — strategy survey: 20 intraday strategies, long and short

`python3 -m algo survey`, report in `reports/survey-latest.md`. List and rules fixed before running:
₹25,000 a trade, 1.5% stop, out by 15:15, Nov 2023 to Oct 2026, about 200 stocks. To pass, net positive
on the first two-thirds of sessions, then a corrected lower bound above zero on the last third.

**Result: none passed, and none was net positive in either period.** The best before charges was gap
and go on up gaps, at +₹1.22 a trade after slippage. Charges are about ₹55 a trade, so every strategy
loses about ₹50 to ₹120 net. Long and short versions of the same idea both lose, which is what costs
look like when a market offers no easy direction to exploit at this size.

Not tested, because the data is not here: options, pairs, news and order-book strategies, delivery or
multi-day holds. Hourly bars cannot show intra-hour timing. Stocks are today's Nifty 200, which
flatters dip-buying, and it still lost.

## 2026-10-30 — almost 3 years of hourly data, about 200 stocks

Pass rule set first: 100+ model picks on unseen sessions, and a 95% lower bound on net R above zero.
First-hour breakouts, hold to the close, Nov 2023 to Oct 2026, 703 sessions, 42,187 signals.
`python3 -m algo weekly` repeats this. Report: `reports/longtest-latest.md`.

- All signals: −0.052R gross (interval −0.056R to −0.048R), −0.188R net.
- Volume 2x normal: −0.041R gross, −0.153R net. Volume 4x normal: −0.037R gross, −0.134R net. The
  stocks-in-play filter does help a little, but stays negative before charges.
- Every 6-month period was negative before charges.
- 28,113 unseen signals: −0.055R gross, −0.194R net. The model picked none. **Fails.**

Across several market conditions, these long-only breakouts sit near zero before charges, and charges
decide the result. That points at trade cost and frequency as much as at entries. Hourly bars are
coarser than the live 5-minute rules, so this is a general check, not a test of the live strategies.

## 2026-10-30 — wider market: Nifty 200 instead of 25 names

Same model, features, threshold and pass rule, on all 200 Nifty 200 stocks over 59 sessions, using
all 5 entries without the regime filter. One-off run, not part of the scheduled reports.

- 12,584 signals: −0.185R gross (95% interval −0.199R to −0.171R), −0.447R net.
- 7,031 unseen signals: −0.195R gross, −0.456R net. The model picked 1 of them. **Fails.**
- Rough stocks-in-play check: ORB signals on a bar with 3x+ the day's median volume. 1,241 signals,
  −0.191R gross. Last 21 sessions: 342 signals, −0.192R gross. This uses volume within the day, not
  against each stock's history, so it is not the published method.

With 25 times more evidence the interval is tight, and it sits well below zero. More data did not
reveal a pattern. These are 5-minute bars from one 59-session period.

## 2026-10-30 — full rerun on freshly downloaded data, plus a stability test

Same result on fresh prices (59 complete sessions): no variant passes. Baseline 66 trades, net
−₹4,504. Signal study −0.204R gross. Walk-forward 32 unseen trades, −₹2,895. Learned filter picked 2
of 782 unseen signals, and both lost. Nothing was tuned, because tuning on this data would be
curve-fitting. `python3 -m algo stability` passes: see `reports/stability-latest.md`. That result is
about the software only.

## 2026-10-30 — round 3: a learned signal filter, pre-registered before running

`python3 -m algo learn`: ridge regression on features known at the signal bar, predicting gross R,
across all 5 entries without the regime filter. Fitted only on earlier sessions (30 minimum), refitted
every 10, scored on unseen ones. It takes a signal when predicted gross R is above 0.28.

**Pass rule, set in advance:** 30+ picked unseen signals, and a 95% lower bound on net R above zero.
One model, one threshold, one run. The penalty and features are not changed after seeing the result.

**Result: fails. The model found nothing it could use.** Of 810 unseen signals (average −0.204R
gross, −0.487R net), it predicted +0.28R or better for only 4, and those averaged −0.331R gross and
−0.464R net. Four signals prove nothing about the model, but a filter that almost never fires has no
pattern to trade. A test in `tests/` confirms the same code does find a pattern when one exists.
Limits: 60 sessions, one market period, linear model. A bigger model on this little data would only
memorise it. Nothing here reaches the engine.

## 2026-10-30 — round 2: three new entries, pre-registered before running

Tested with `python3 -m algo signals --strategies <name>`, with parameters fixed in `config.json`:
`pullback` (strong open, first dip to VWAP that holds), `vwap_revert` (1%+ below VWAP, then a bar
closes above the prior high, target VWAP, run with `--no-regime`), `afternoon_high` (new day high
after 13:00 on a stock up 1%+, above VWAP).

**Pass rule, set in advance:** with 3 tries, the out-of-sample average **net** R must be above zero,
and the 95% lower bound on all-sample gross R must be above the cost of about 0.28R. Passing only
earns a backtest and forward paper trading. No parameter is changed after seeing a result.

**Result: all three fail. `config.json` keeps `orb` and `vwap_reclaim`, and none goes live on paper.**

| entry | signals | gross R (95% interval) | out-of-sample net R |
|---|---|---|---|
| `pullback` | 139 | −0.231 (−0.350 to −0.112) | −0.572 |
| `afternoon_high` | 94 | −0.114 (−0.212 to −0.016) | −0.310 |
| `vwap_revert` | 72 | −0.084 (−0.281 to +0.112) | −0.333 |

None came close to the +0.28R gross needed. `vwap_revert` is the least bad but has few signals and a
wide interval, so it shows nothing either way. Long-only intraday entries on these 25 names have not
worked in this 60-session period, and more variants on the same data would only be curve-fitting.

## 2026-10-30 — signal study and walk-forward: the entries themselves lose

Added a 0.01% half spread, then measured every signal without portfolio limits (472 signals against
66 backtest trades, same 60 sessions). Reports: `reports/signals-latest.md`, `reports/walkforward-latest.md`.

**The orb and vwap_reclaim entries do not have an edge in this period, even before charges.**

- Gross: −0.204R a signal, 95% interval −0.271R to −0.136R. Charges add about 0.28R on top. Both
  splits are negative: in-sample −0.250R, out-of-sample −0.128R. This settles what 71 trades could
  not: the gross result is below zero, not merely unproven.
- By strategy: orb −0.183R, vwap_reclaim −0.229R. Both intervals sit below zero.
- Targets are reachable: 48 of 472 signals hit them. There are just too many stops (273).
- Walk-forward: 45 unseen trades, net −₹3,351.71, −0.322R. Fails the gate. Picking the best past
  variant did not carry forward.
- `rs_filter`, the one positive out-of-sample result in the rerun below, went to −₹2.83 a trade once
  the spread was added. It was noise. Do not pursue it on that evidence.
- 09:xx entries are the least bad (−0.048R, interval −0.225R to +0.129R). This was not
  pre-registered and is still negative after charges, so it is a lead at most.

**What this means:** stop tuning these two strategies. Changing exits or filters cannot repair a
negative gross entry. A new idea should beat about +0.28R gross in `python3 -m algo signals` before
any portfolio test. One 60-session period cannot prove these never work, and longer data is still
the most valuable next step.

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
2. **The gross result was not distinguishable from zero on these trades.** Gross was about −₹24 a trade, or −0.13R
   with a standard error of 0.09R. Charges (about ₹49 a trade, roughly 0.23R) make the net result
   clearly negative: −0.36R, 95% CI −0.53R to −0.20R. *Corrected 2026-10-30: this said there was
   no gross edge, which 71 trades cannot show either way. The signal study above now shows it.*
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
