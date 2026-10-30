import json
import os
import unittest
from datetime import timedelta
from unittest import mock

from algo import commands, research
from algo.broker.base import Broker
from algo.broker.paper import PaperBroker
from algo.costs import CostModel
from algo.engine import new_state
from algo.models import Position, slip_pct
from tests.helpers import D, cfg, day, flat
from tests.test_engine import BREAK, INDEX_UP, RANGE, one_symbol_cfg

ENV = {"TELEGRAM_BOT_TOKEN": "T", "TELEGRAM_CHAT_ID": "-100123"}


def state():
    c = cfg()
    s = new_state(c)
    s["date"] = D.isoformat()
    return c, s


class CommandTests(unittest.TestCase):
    def test_every_command_answers_on_an_empty_state(self):
        c, s = state()
        for name in commands.COMMANDS:
            self.assertTrue(commands.answer("/" + name, s, c, False))

    def test_plain_text_is_ignored(self):
        c, s = state()
        self.assertIsNone(commands.answer("hello", s, c, False))

    def test_bot_suffix_and_case(self):
        c, s = state()
        self.assertIn("Equity", commands.answer("/STATUS@Paper_Ayu_Bot", s, c, False))

    def test_unknown_command(self):
        c, s = state()
        self.assertIn("/help", commands.answer("/nope", s, c, False))

    def test_positions_and_kill_switch_shown(self):
        c, s = state()
        s["positions"]["SBIN"] = Position("SBIN", "orb", 10, 800.0, 795.0, 818.0, "", 60.0, "").to_dict()
        self.assertIn("SBIN", commands.answer("/positions", s, c, False))
        self.assertIn("ON", commands.answer("/status", s, c, True))

    def test_pnl_lists_history(self):
        c, s = state()
        s["history"] = {"2026-10-26": {"net": -120.5, "trades": 2}}
        self.assertIn("-120.50", commands.answer("/pnl", s, c, False))

    def run_process(self, updates):
        c, s = state()
        calls = []

        def fake(token, offset=None):
            calls.append(offset)
            return updates if offset is None else []
        with mock.patch.dict(os.environ, ENV), mock.patch.object(commands, "_get_updates", fake), \
                mock.patch.object(commands, "telegram") as tg:
            n = commands.process(s, c, False)
        return n, tg, calls

    def test_answers_the_channel_then_marks_read(self):
        up = [{"update_id": 7, "channel_post": {"chat": {"id": -100123}, "text": "/status"}}]
        n, tg, calls = self.run_process(up)
        self.assertEqual(n, 1)
        self.assertEqual(calls, [None, 8])

    def test_other_chats_are_ignored_but_marked_read(self):
        up = [{"update_id": 9, "message": {"chat": {"id": 555}, "text": "/status"}}]
        n, tg, calls = self.run_process(up)
        self.assertEqual(n, 0)
        tg.assert_not_called()
        self.assertEqual(calls, [None, 10])

    def test_telegram_failure_does_not_raise(self):
        c, s = state()
        with mock.patch.dict(os.environ, ENV), mock.patch.object(commands, "_get_updates", side_effect=OSError):
            self.assertEqual(commands.process(s, c, False), 0)

    def test_no_secrets_no_calls(self):
        c, s = state()
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}):
            self.assertEqual(commands.process(s, c, False), 0)


class SpreadAndBrokerTests(unittest.TestCase):
    def test_spread_adds_to_slippage(self):
        self.assertAlmostEqual(slip_pct(cfg()), 0.06)

    def test_paper_broker_is_a_broker(self):
        self.assertIsInstance(PaperBroker(CostModel(cfg()["costs"]), 0.05, 0.05), Broker)


class ResearchTests(unittest.TestCase):
    def hist(self, n=6):
        h = {"X": [], "^NSEI": []}
        for k in range(n):
            d = D + timedelta(days=k)
            tail = [(102.6, 108, 102.5, 107.5, 4000)] if k % 2 == 0 else [(102.6, 102.7, 100.5, 100.8, 4000)]
            h["X"] += day(d, RANGE + BREAK + tail + flat(101, 3))
            h["^NSEI"] += day(d, INDEX_UP[:10])
        return h

    def test_counts_every_signal_with_gross_and_net(self):
        rows = research.signal_rows(one_symbol_cfg(), self.hist())
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r["r_multiple"] < r["gross_r"] for r in rows))

    def test_ignores_position_limits(self):
        c = one_symbol_cfg(max_open_positions=0)
        self.assertEqual(len(research.signal_rows(c, self.hist())), 6)

    def test_red_index_is_filtered(self):
        h = self.hist(1)
        h["^NSEI"] = day(D, [(25000, 25000, 24900, 24950, 0)] * 10)
        self.assertEqual(research.signal_rows(one_symbol_cfg(), h), [])

    def test_report_renders(self):
        rep = research.signal_study(one_symbol_cfg(), self.hist())
        self.assertIn("Signal study", research.study_markdown(rep))
        self.assertEqual(rep["slices"][0][1]["signals"], 6)

    def test_walk_forward_only_scores_unseen_days(self):
        vs = [{"name": "a", "set": {}}, {"name": "b", "set": {"orb": {"target_r": 2.0}}}]
        rep = research.walk_forward(one_symbol_cfg(), self.hist(12), vs, train=4, test=2)
        self.assertEqual(rep["folds"], [])  # under 10 training trades: nothing is picked
        self.assertIn("Walk-forward", research.walk_markdown(rep, 4, 2))
        rep = research.walk_forward(one_symbol_cfg(), self.hist(22), vs, train=12, test=4)
        self.assertTrue(rep["folds"])
        self.assertLessEqual(rep["unseen"]["trades"], 8)


if __name__ == "__main__":
    unittest.main()


class NewStrategyTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg()

    def test_pullback_needs_a_strong_open(self):
        from algo.strategies.pullback import pullback
        rows = [(100, 101.5, 100, 101.2, 4000)] * 9 + [(100.6, 101.1, 100.2, 101, 2000)]
        self.assertIsNotNone(pullback("X", day(D, rows), self.cfg))
        weak = [(100, 100.2, 99.9, 100.1, 4000)] * 9 + [(100.1, 100.3, 99.8, 100.2, 2000)]
        self.assertIsNone(pullback("X", day(D, weak), self.cfg))

    def test_revert_targets_vwap(self):
        from algo.strategies.vwap_revert import vwap_revert
        rows = [(102, 102.5, 101.5, 102, 9000)] * 9 + [(100, 100.2, 99.5, 99.8, 1000), (99.8, 100.4, 99.7, 100.3, 1000)]
        s = vwap_revert("X", day(D, rows), self.cfg)
        self.assertIsNotNone(s)
        self.assertGreater(s.target, s.entry)

    def test_afternoon_high_waits_for_the_afternoon(self):
        from algo.strategies.afternoon_high import afternoon_high
        rows = [(100, 101, 100, 100.9, 1000)] * 47 + [(100.9, 103, 100.9, 102.5, 1000)]
        s = afternoon_high("X", day(D, rows), self.cfg)
        self.assertIsNotNone(s)
        self.assertGreaterEqual(s.bar_ts.strftime("%H:%M"), "13:00")


class LearnTests(unittest.TestCase):
    def test_ridge_recovers_a_line(self):
        from algo.learn import predict, ridge
        X = [[1.0, float(i)] for i in range(20)]
        w = ridge(X, [2 + 3 * r[1] for r in X], lam=0.0)
        self.assertAlmostEqual(predict(w, [1.0, 10.0]), 32.0, places=6)

    def row(self, day_i, f, y):
        return {"date": "2026-%02d-%02d" % (8 + day_i // 28, 1 + day_i % 28), "x": [f], "gross_r": y, "r_multiple": y - 0.3,
                "exit_reason": "stop", "net_pnl": y, "gross_pnl": y, "charges": 1.0}

    def test_walk_finds_a_real_pattern_and_never_scores_training_days(self):
        from algo.learn import walk
        rows = [self.row(d, f, 2.0 * f) for d in range(50) for f in (-1.0, 1.0)]
        rep = walk(rows, min_train=30, step=10)
        self.assertEqual(rep["unseen"]["signals"], 40)
        self.assertEqual(rep["picked"]["signals"], 20)
        self.assertGreater(rep["picked"]["avg_gross_r"], 1.5)
