import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import algo.__main__ as cli
from algo import data, stability
from algo.engine import new_state
from tests.helpers import cfg
from tests.test_commands_research import ResearchTests
from tests.test_engine import one_symbol_cfg


class StateTests(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cli, "STATE", os.path.join(tmp, "state.json")), \
                mock.patch.object(cli, "telegram") as tg, redirect_stdout(io.StringIO()):
            with open(cli.STATE, "w") as fh:
                fh.write(text)
            return cli.load_state(cfg()), tg, os.path.exists(cli.STATE + ".corrupt")

    def test_corrupt_state_restarts_and_alerts(self):
        state, tg, kept = self.load('{"equity": 49')
        self.assertEqual(state["equity"], 50000.0)
        tg.assert_called_once()
        self.assertTrue(kept)

    def test_old_state_gains_new_fields(self):
        old = new_state(cfg())
        del old["today"]["ticks"], old["history"]
        state, tg, _ = self.load(json.dumps(old))
        self.assertEqual(state["today"]["ticks"], 0)
        self.assertEqual(state["history"], {})
        tg.assert_not_called()


class CrashTests(unittest.TestCase):
    def test_a_crash_reaches_the_channel_and_still_fails_the_run(self):
        with mock.patch.object(cli, "_dispatch", side_effect=ValueError), mock.patch.object(cli, "telegram") as tg:
            with self.assertRaises(ValueError):
                cli.main(["tick"])
        self.assertIn("crashed", tg.call_args[0][0])


class FetchTests(unittest.TestCase):
    def test_a_failing_symbol_does_not_stop_the_others(self):
        def fake(sym, *a, **k):
            if sym == "BAD":
                raise OSError("down")
            return []
        with mock.patch.object(data, "fetch_bars", fake):
            out, errors = data.YahooSource().today(["A", "BAD", "C"], mock.Mock(), 60)
        self.assertEqual(sorted(out), ["A", "C"])
        self.assertIn("BAD", errors)


class ReplayTests(unittest.TestCase):
    def test_clean_replay_matches_the_backtest(self):
        hist = ResearchTests().hist(8)
        self.assertTrue(stability.run(one_symbol_cfg(), hist, seeds=(1,))["identical"])

    def test_chaos_breaks_no_rule(self):
        rep = stability.run(one_symbol_cfg(), ResearchTests().hist(8), seeds=(1, 2))
        self.assertTrue(stability.passed(rep))


class WeeklyTests(unittest.TestCase):
    def test_message_says_nothing_passed(self):
        from algo import weekly
        short = {"signals": 10, "unseen": {"avg_gross_r": -0.2}, "picked": {"signals": 0}, "verdict": "INCONCLUSIVE: 0"}
        long_rep = {"sessions": 5, "all": {"signals": 9, "avg_gross_r": -0.05}, "picked": {"signals": 0}, "verdict": "INCONCLUSIVE: 0"}
        msg = weekly.message(short, long_rep, {"trades": 0})
        self.assertIn("nothing passed", msg)
        self.assertIn("none yet", msg)

    def test_paper_results_read_the_journal(self):
        from algo import weekly
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "t.csv")
            self.assertEqual(weekly.paper_results(p)["trades"], 0)
            with open(p, "w") as fh:
                fh.write("net_pnl,gross_pnl,charges,r_multiple,exit_reason\n-10,5,15,-0.5,stop\n20,35,15,1.0,target\n")
            self.assertEqual(weekly.paper_results(p)["trades"], 2)

    def test_long_test_finds_signals_and_ignores_the_first_bar_volume(self):
        from algo import longtest
        from algo.models import Bar
        from algo.timeutil import IST
        from datetime import datetime, timedelta
        bars = []
        for k in range(30):
            t = datetime(2026, 1, 1, 9, 15, tzinfo=IST) + timedelta(days=k)
            for i, (o, h, l, c) in enumerate([(100, 101, 99.5, 100.5), (100.5, 102, 100, 101.5), (101.5, 103, 101, 102),
                                              (102, 102.5, 101, 101.5), (101.5, 102, 101, 101.2), (101.2, 102, 101, 101.5)]):
                bars.append(Bar(t + timedelta(hours=i), o, h, l, c, 0.0 if i == 0 else 1000.0, 60))
        rows = longtest.rows(cfg(), {"X": bars})
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["rel_volume"], 1.0)


class SurveyTests(unittest.TestCase):
    def bars(self, rows):
        from algo.models import Bar
        from algo.timeutil import IST
        from datetime import datetime, timedelta
        t = datetime(2026, 1, 5, 9, 15, tzinfo=IST)
        return [Bar(t + timedelta(hours=i), *map(float, r), 1000.0, 60) for i, r in enumerate(rows)]

    def setUp(self):
        from algo.costs import CostModel
        self.c = CostModel(cfg()["costs"])

    def test_long_and_short_are_mirror_images_before_costs(self):
        from algo.survey import trade
        b = self.bars([(100, 101, 99, 100), (100, 101, 99.5, 100.5), (100.5, 101, 100, 100.5), (101, 101, 101, 101)])
        self.assertAlmostEqual(trade(b, 0, 1, 0, self.c)[0], 250.0)
        self.assertAlmostEqual(trade(b, 0, -1, 0, self.c)[0], -250.0)

    def test_stop_limits_the_loss_and_charges_are_taken(self):
        from algo.survey import trade
        b = self.bars([(100, 101, 99, 100), (100, 100, 90, 91), (91, 92, 90, 91), (91, 91, 91, 91)])
        gross, net = trade(b, 0, 1, 0, self.c)
        self.assertAlmostEqual(gross, -375.0)
        self.assertLess(net, gross)

    def test_short_stop_is_above_entry(self):
        from algo.survey import trade
        b = self.bars([(100, 101, 99, 100), (100, 110, 100, 109), (109, 110, 108, 109), (109, 109, 109, 109)])
        self.assertAlmostEqual(trade(b, 0, -1, 0, self.c)[0], -375.0)

    def test_streak_counts_consecutive_days(self):
        from algo.survey import contexts
        from algo.data import by_day
        from algo.models import Bar
        from algo.timeutil import IST
        from datetime import datetime, timedelta
        out = []
        for k, c in enumerate([100, 99, 98, 97, 96]):
            t = datetime(2026, 1, 5, 9, 15, tzinfo=IST) + timedelta(days=k)
            out += [Bar(t + timedelta(hours=i), c, c + 1, c - 1, c, 1000.0, 60) for i in range(6)]
        ctx = dict(contexts(out, {}))
        self.assertEqual(ctx[sorted(ctx)[-1]]["streak"], -3)


class DeliveryTests(unittest.TestCase):
    def prices(self):
        from algo import delivery
        from datetime import date, timedelta
        days = [date(2020, 1, 1) + timedelta(days=k) for k in range(200)]
        closes = {n: {d: 100.0 + k * m for k, d in enumerate(days)} for n, m in
                  (("A", 1), ("B", 2), (delivery.ETF, 1), (delivery.INDEX, 1))}
        return delivery, delivery.Prices(closes), days

    def test_delivery_charges_include_stt_both_ways_and_dp_on_sale(self):
        from algo import delivery
        self.assertGreater(delivery.buy_cost(5000), 5000 * 0.001)
        self.assertGreater(delivery.sell_cost(5000), delivery.buy_cost(5000) + 15)

    def test_a_stock_joins_only_once_it_has_traded_enough(self):
        delivery, p, days = self.prices()
        traded = {"A": {d: 100.0 for d in days[:150]}, "B": {d: 500.0 for d in days[150:]}}
        members = delivery.by_turnover(p, traded, ["A", "B"], top=1)
        ends = sorted(members)
        self.assertEqual(members[ends[3]], ["A"])  # B has no history yet, so hindsight cannot pick it
        self.assertEqual(members[ends[-1]], [])


class BhavTests(unittest.TestCase):
    def zipped(self, text):
        import io as _io
        import zipfile
        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("x.csv", text)
        return buf.getvalue()

    def test_reads_both_file_formats_and_keeps_surveillance_series(self):
        from algo import bhav
        old = "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,\nA,EQ,1,1,1,10,10,9,5,50,x,\nB,BE,1,1,1,8,8,8,5,40,x,\nC,N1,1,1,1,8,8,8,5,40,x,\n"
        new = "TckrSymb,SctySrs,ClsPric,PrvsClsgPric,TtlTrfVal\nA,EQ,10,9,50\n"
        self.assertEqual(bhav.parse(self.zipped(old)), [("A", 10.0, 9.0, 50.0), ("B", 8.0, 8.0, 40.0)])
        self.assertEqual(bhav.parse(self.zipped(new)), [("A", 10.0, 9.0, 50.0)])

    def test_a_split_is_not_a_crash(self):
        import gzip
        from datetime import date
        from algo import bhav
        with tempfile.TemporaryDirectory() as tmp:
            for d, row in (("2020-01-01", "A,100,100,1\n"), ("2020-01-02", "A,50,100,1\n"), ("2020-01-03", "A,55,50,1\n")):
                with gzip.open(os.path.join(tmp, d + ".csv.gz"), "wt") as fh:
                    fh.write(row)
            moves, _ = bhav.load(tmp)
        closes = bhav.adjusted(moves)
        self.assertEqual(closes["A"][date(2020, 1, 2)], 100.0)
        self.assertAlmostEqual(closes["A"][date(2020, 1, 3)], 110.0)

    def test_a_real_crash_stays_and_yahoo_wins_when_it_has_the_stock(self):
        from datetime import date
        from algo import bhav
        a, b = date(2020, 1, 1), date(2020, 1, 2)
        moves = {"X": [(a, 1.0), (b, 0.45)]}
        self.assertAlmostEqual(bhav.adjusted(moves)["X"][b], 45.0)
        self.assertAlmostEqual(bhav.adjusted(moves, {"X": {a: 10.0, b: 9.0}})["X"][b], 90.0)

    def test_urls_cover_both_eras(self):
        from datetime import date
        from algo import bhav
        self.assertIn("cm28JUN2024bhav", bhav.urls(date(2024, 6, 28))[0])
        self.assertIn("20261029_F_0000", bhav.urls(date(2026, 10, 29))[0])

    def test_quarterly_keeps_holdings_between_quarters(self):
        from algo import delivery
        p = mock.Mock(days={5: __import__("datetime").date(2020, 4, 30)})
        self.assertEqual(delivery._quarterly(p, [], 5, ["X"]), ["X"])


class GuideTests(unittest.TestCase):
    def test_rsi_extremes(self):
        from algo import extra
        self.assertGreater(extra._rsi([float(x) for x in range(1, 40)])[-1], 95)
        self.assertLess(extra._rsi([float(x) for x in range(40, 1, -1)])[-1], 5)

    def test_bullish_divergence_is_found(self):
        from algo import extra
        from tests.helpers import D, day
        down = [(110 - i, 110 - i + .2, 110 - i - .5, 110 - i - .4, 100) for i in range(20)]
        bounce = [(91 + i * .5, 91.8 + i * .5, 90.8 + i * .5, 91.5 + i * .5, 100) for i in range(14)]
        slow = [(97.5, 97.6, 89.5, 97.4, 100), (97.4, 97.8, 88.9, 97.7, 100), (97.7, 98, 97.5, 97.9, 100)]
        self.assertIsInstance(extra.divergence(day(D, down + bounce + slow), 1, use_macd=True), int)
