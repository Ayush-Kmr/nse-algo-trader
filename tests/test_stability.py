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
