import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import timedelta
from unittest import mock

import algo.__main__ as cli
from algo import backtest as bt
from algo import notify
from algo.costs import CostModel
from algo.data import completed
from algo.engine import Engine, new_state
from algo.models import Position, Signal
from algo.report import expected_ticks
from algo.risk import check_entry
from algo.sizing import size_position
from tests.helpers import D, at, cfg, day, flat
from tests.test_engine import BREAK, INDEX_UP, RANGE, one_symbol_cfg
from tests.test_risk import acct


class CompletedBarTests(unittest.TestCase):
    def setUp(self):
        self.bars = day(D, flat(100, 3))  # 09:15, 09:20, 09:25

    def test_just_ended_last_bar_waits_for_grace(self):
        self.assertEqual(len(completed(self.bars, at(D, "09:30"), 60)), 2)
        self.assertEqual(len(completed(self.bars, at(D, "09:31"), 60)), 3)

    def test_later_bar_makes_a_bar_final(self):
        self.assertEqual(len(completed(self.bars, at(D, "09:25"), 60)), 2)

    def test_forming_bar_is_never_used(self):
        self.assertEqual(len(completed(self.bars, at(D, "09:29"), 0)), 2)


class CostAndRiskFixTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg()
        self.c = CostModel(self.cfg["costs"])

    def test_minimum_brokerage(self):
        self.assertEqual(float(self.c.brokerage(1000)), 5.0)
        self.assertEqual(float(self.c.brokerage(0)), 0.0)

    def test_no_cash_is_not_reported_as_a_far_stop(self):
        s = size_position(500, 495, 250, self.c, 0.05, 100)
        self.assertEqual(s.qty, 0)
        self.assertIn("no cash", s.limited_by)

    def test_cost_ratio_uses_the_shrunk_budget(self):
        sig = Signal("SBIN", "orb", 800.0, 795.0, 818.0, at(D, "09:35"), "test")
        v = check_entry(sig, acct(realised_today=-300), self.cfg, self.c, at(D, "10:00"))
        self.assertFalse(v.ok)
        self.assertTrue(any("charges are" in r for r in v.reasons), v.reasons)

    def test_minimum_position_value(self):
        c = cfg(min_position_value=40000)
        sig = Signal("SBIN", "orb", 800.0, 795.0, 818.0, at(D, "09:35"), "test")
        v = check_entry(sig, acct(), c, self.c, at(D, "10:00"))
        self.assertTrue(any("below the minimum" in r for r in v.reasons), v.reasons)


class LateTickTests(unittest.TestCase):
    def run_late(self, later):
        c = one_symbol_cfg()
        state = new_state(c)
        sym = day(D, RANGE + BREAK + later)
        ev = Engine(c, state).step(sym[-1].end, {"X": sym}, day(D, INDEX_UP[:len(sym)]))
        return state, ev

    def test_late_fill_uses_the_latest_close(self):
        state, _ = self.run_late([(102.6, 102.8, 102.5, 102.7, 3000)])
        self.assertGreaterEqual(state["positions"]["X"]["entry_price"], 102.7)
        self.assertEqual(state["positions"]["X"]["last_bar_ts"][11:16], "09:35")

    def test_price_ran_away_is_not_chased(self):
        state, ev = self.run_late([(102.6, 103.9, 102.5, 103.8, 3000)])
        self.assertEqual(state["positions"], {})
        self.assertEqual(ev[0]["kind"], "EXPIRED")


class LiveGuardTests(unittest.TestCase):
    def setUp(self):
        self.c = one_symbol_cfg()
        self.state = new_state(self.c)
        self.sent = []
        self.eng = Engine(self.c, self.state, notify=self.sent.append)
        self.sym = day(D, RANGE + BREAK)
        self.idx = day(D, INDEX_UP[:4])

    def test_start_and_tick_count(self):
        self.eng.step(at(D, "09:32"), {"X": self.sym[:3]}, self.idx[:3], live=True)
        self.eng.step(at(D, "09:37"), {"X": self.sym}, self.idx, live=True)
        self.assertEqual(self.state["today"]["ticks"], 2)
        self.assertEqual([e["kind"] for e in self.sent].count("START"), 1)

    def test_backup_tick_right_after_a_primary_is_not_counted(self):
        self.eng.step(at(D, "09:32"), {"X": self.sym[:3]}, self.idx[:3], live=True)
        self.eng.step(at(D, "09:33"), {"X": self.sym[:3]}, self.idx[:3], live=True)
        self.assertEqual(self.state["today"]["ticks"], 1)

    def test_backtest_steps_are_not_counted(self):
        self.eng.step(at(D, "09:35"), {"X": self.sym}, self.idx)
        self.assertEqual(self.state["today"]["ticks"], 0)

    def test_gap_is_alerted(self):
        self.eng.step(at(D, "09:32"), {"X": self.sym[:3]}, self.idx[:3], live=True)
        self.eng.step(at(D, "10:02"), {"X": self.sym}, self.idx, live=True)
        self.assertIn("GAP", [e["kind"] for e in self.sent])

    def test_late_first_tick_is_a_gap(self):
        self.eng.step(at(D, "11:00"), {"X": self.sym}, self.idx, live=True)
        self.assertIn("GAP", [e["kind"] for e in self.sent])

    def test_stale_data_blocks_entries(self):
        self.eng.step(at(D, "10:00"), {"X": self.sym}, self.idx, live=True)
        self.assertEqual(self.state["positions"], {})
        self.assertTrue(any("stale" in e["msg"] for e in self.sent))

    def test_open_position_without_data_alerts_once_then_critical_at_square_off(self):
        self.state["date"] = D.isoformat()
        self.state["positions"]["X"] = Position("X", "orb", 10, 100.0, 98.0, 110.0, "", 30.0,
                                                self.sym[0].ts.isoformat()).to_dict()
        for hm in ("15:00", "15:05", "15:15", "15:20"):
            self.eng.step(at(D, hm), {}, None)
        kinds = [e["kind"] for e in self.sent]
        self.assertEqual(kinds.count("WARN"), 1)
        self.assertEqual(kinds.count("CRITICAL"), 1)


class GateTests(unittest.TestCase):
    OOS = {"trades": 40, "expectancy_rs": 10.0, "avg_r_net": 0.1, "avg_r_se": 0.1}

    def test_small_positive_average_does_not_pass(self):
        self.assertTrue(bt.verdict(self.OOS).startswith("INCONCLUSIVE"))

    def test_clear_edge_passes(self):
        self.assertTrue(bt.verdict(dict(self.OOS, avg_r_net=0.4)).startswith("PASSES"))

    def test_multiple_tests_raise_the_bar(self):
        oos = dict(self.OOS, avg_r_net=0.25)
        self.assertTrue(bt.verdict(oos).startswith("PASSES"))
        self.assertTrue(bt.verdict(oos, tests=12).startswith("INCONCLUSIVE"))


class TelegramTests(unittest.TestCase):
    ENV = {"TELEGRAM_BOT_TOKEN": "SECRET", "TELEGRAM_CHAT_ID": "@paper_channel"}

    def test_not_configured(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            self.assertFalse(notify.send("x")[0])

    def test_posts_to_the_channel(self):
        with mock.patch.dict(os.environ, self.ENV), mock.patch("urllib.request.urlopen") as op:
            self.assertEqual(notify.send("hello"), (True, "sent"))
        req = op.call_args[0][0]
        self.assertEqual(json.loads(req.data)["chat_id"], "@paper_channel")

    def test_error_gives_telegrams_reason_without_the_token(self):
        err = urllib.error.HTTPError("u", 400, "Bad", {}, io.BytesIO(b'{"description": "chat not found"}'))
        with mock.patch.dict(os.environ, self.ENV), mock.patch("urllib.request.urlopen", side_effect=err):
            ok, why = notify.send("x")
        self.assertFalse(ok)
        self.assertIn("chat not found", why)
        self.assertNotIn("SECRET", why)

    def test_event_format(self):
        msg = notify.format_event({"time": "10:00", "kind": "ENTRY", "symbol": "SBIN", "msg": "buy"})
        self.assertIn("[PAPER]", msg)
        self.assertIn("SBIN", msg)


class EodTests(unittest.TestCase):
    def eod(self, state, now):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(cli, "STATE", os.path.join(tmp, "state.json")), \
                mock.patch.object(cli, "ROOT", tmp), \
                mock.patch.object(cli, "telegram") as tg, redirect_stdout(io.StringIO()):
            cli.save_state(state)
            a = mock.Mock(now=now, quiet=False)
            self.assertEqual(cli.cmd_eod(a, cfg()), 0)
        return tg.call_args[0][0]

    def test_no_tick_today_is_critical(self):
        st = new_state(cfg())
        st["date"] = (D - timedelta(days=1)).isoformat()
        self.assertIn("no tick ran", self.eod(st, "%s 15:45" % D))

    def test_summary_reports_tick_coverage(self):
        st = new_state(cfg())
        st["date"] = D.isoformat()
        st["today"]["ticks"] = 60
        self.assertIn("60/72 ticks", self.eod(st, "%s 15:45" % D))

    def test_second_run_does_not_post_again(self):
        st = new_state(cfg())
        st["date"] = D.isoformat()
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(cli, "STATE", os.path.join(tmp, "state.json")), \
                mock.patch.object(cli, "ROOT", tmp), \
                mock.patch.object(cli, "telegram") as tg, redirect_stdout(io.StringIO()):
            cli.save_state(st)
            a = mock.Mock(now="%s 15:45" % D, quiet=False)
            cli.cmd_eod(a, cfg())
            cli.cmd_eod(a, cfg())
        self.assertEqual(tg.call_count, 1)

    def test_expected_ticks(self):
        self.assertEqual(expected_ticks(cfg()), 72)


if __name__ == "__main__":
    unittest.main()
