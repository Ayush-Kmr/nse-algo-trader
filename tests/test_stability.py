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
