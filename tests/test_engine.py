import unittest
from datetime import timedelta

from algo import backtest as bt
from algo.broker.paper import PaperBroker
from algo.costs import CostModel
from algo.engine import Engine, new_state
from algo.models import Position
from tests.helpers import D, at, cfg, day, flat

RANGE = [(100, 102, 100, 101, 5000), (101, 101.5, 100.2, 101, 2000), (101, 101.8, 100.5, 101.2, 2000)]
BREAK = [(101.2, 103, 101.1, 102.6, 6000)]                     # 09:30 bar closes above 102
INDEX_UP = [(25000, 25010, 24990, 25005, 0)] + [(25005, 25020, 25000, 25015, 0)] * 80


def one_symbol_cfg(**kw):
    return cfg(universe=["X"], strategies=["orb"], **kw)


def run_day(rows, c=None, kill=False):
    c = c or one_symbol_cfg()
    state = new_state(c)
    eng = Engine(c, state)
    sym = day(D, rows)
    idx = day(D, INDEX_UP)
    events = []
    for i in range(len(sym)):
        now = sym[i].end
        events += eng.step(now, {"X": sym[:i + 1]}, idx[:i + 1], kill_switch=kill)
    return state, events


class PaperBrokerTests(unittest.TestCase):
    def setUp(self):
        self.b = PaperBroker(CostModel(cfg()["costs"]), 0.05, 0.05)
        self.p = Position("X", "orb", 10, 100.0, 98.0, 104.0, "", 30.0, "")

    def bar(self, o, h, l, c):
        return day(D, [(o, h, l, c, 1)])[0]

    def test_stop_wins_when_both_touched(self):
        self.assertEqual(self.b.check_bar(self.p, self.bar(100, 105, 97, 101))[1], "stop")

    def test_gap_through_stop_fills_at_open(self):
        px, why = self.b.check_bar(self.p, self.bar(96, 97, 95, 96))
        self.assertEqual(why, "stop (gap)")
        self.assertLess(px, 96)

    def test_target(self):
        self.assertEqual(self.b.check_bar(self.p, self.bar(101, 104.5, 100.5, 104)), (104.0, "target"))

    def test_close_is_net_of_charges(self):
        tr = self.b.close(self.p, 104.0, "target", at(D, "11:00"))
        self.assertEqual(tr.gross_pnl, 40.0)
        self.assertLess(tr.net_pnl, tr.gross_pnl)
        self.assertAlmostEqual(tr.net_pnl, tr.gross_pnl - tr.charges, places=2)


class EngineTests(unittest.TestCase):
    def test_breakout_then_target(self):
        rows = RANGE + BREAK + [(102.6, 108, 102.5, 107.5, 4000)] + flat(107.5, 5)
        state, events = run_day(rows)
        kinds = [e["kind"] for e in events]
        self.assertEqual(kinds[:2], ["ENTRY", "EXIT"])
        tr = state["today"]["trades"][0]
        self.assertEqual(tr["exit_reason"], "target")
        self.assertGreater(tr["net_pnl"], 0)
        self.assertEqual(state["equity"], round(50000 + tr["net_pnl"], 2))
        self.assertEqual(state["positions"], {})

    def test_square_off_at_1515(self):
        rows = RANGE + BREAK + flat(102.7, 75)  # drifts sideways all day
        state, events = run_day(rows)
        tr = state["today"]["trades"][0]
        self.assertEqual(tr["exit_reason"], "square-off")
        self.assertEqual(tr["exit_ts"][11:16], "15:15")

    def test_kill_switch_blocks_entries(self):
        state, events = run_day(RANGE + BREAK + flat(103, 5), kill=True)
        self.assertEqual(state["today"]["trades"], [])
        self.assertEqual(state["positions"], {})
        self.assertIn("KILL", [e["kind"] for e in events])

    def test_red_index_pauses_longs(self):
        c = one_symbol_cfg()
        state = new_state(c)
        eng = Engine(c, state)
        sym = day(D, RANGE + BREAK)
        idx = day(D, [(25000, 25000, 24900, 24950, 0)] * 4)
        ev = eng.step(sym[-1].end, {"X": sym}, idx)
        self.assertEqual(state["positions"], {})
        self.assertIn("longs paused", ev[0]["msg"])

    def test_stale_signal_expires(self):
        c = one_symbol_cfg()
        state = new_state(c)
        eng = Engine(c, state)
        sym = day(D, RANGE + BREAK + flat(102.8, 4))  # signal at 09:30, now 4 bars later
        ev = eng.step(sym[-1].end, {"X": sym}, day(D, INDEX_UP[:8]))
        self.assertEqual(ev[0]["kind"], "EXPIRED")

    def test_day_roll_archives_history(self):
        state, _ = run_day(RANGE + BREAK + [(102.6, 108, 102.5, 107.5, 4000)])
        eng = Engine(one_symbol_cfg(), state)
        eng.roll_day(at(D + timedelta(days=1), "09:20"))
        self.assertIn(D.isoformat(), state["history"])
        self.assertEqual(state["today"]["trades"], [])


class BacktestTests(unittest.TestCase):
    def test_deterministic_and_net(self):
        c = one_symbol_cfg()
        hist = {"X": [], "^NSEI": []}
        for k in range(5):
            d = D + timedelta(days=k)
            win = k % 2 == 0
            tail = [(102.6, 108, 102.5, 107.5, 4000)] if win else [(102.6, 102.7, 100.5, 100.8, 4000)]
            hist["X"] += day(d, RANGE + BREAK + tail + flat(101, 3))
            hist["^NSEI"] += day(d, INDEX_UP[:10])
        r1 = bt.run(c, hist, "^NSEI")
        r2 = bt.run(c, hist, "^NSEI")
        self.assertEqual(r1["trades"], r2["trades"])
        self.assertEqual(len(r1["trades"]), 5)
        m = bt.metrics(r1["trades"])
        self.assertLess(m["net_total"], m["gross_total"])
        self.assertIn("INCONCLUSIVE", bt.split_report(r1)["verdict"])
        self.assertIn("Backtest report", bt.to_markdown(bt.split_report(r1), c))


if __name__ == "__main__":
    unittest.main()


class StopRatchetTests(unittest.TestCase):
    def setUp(self):
        self.b = PaperBroker(CostModel(cfg()["costs"]), 0.05, 0.05)

    def pos(self):
        return Position("X", "orb", 10, 100.0, 98.0, 110.0, "", 30.0, "")

    def bar(self, h):
        return day(D, [(h - 1, h, h - 1.5, h - 0.5, 1)])[0]

    def test_breakeven_after_1r(self):
        p = self.pos()
        self.b.update_stop(p, self.bar(101.5), {"breakeven_at_r": 1.0})
        self.assertEqual(p.stop, 98.0)
        self.b.update_stop(p, self.bar(102.1), {"breakeven_at_r": 1.0})
        self.assertEqual(p.stop, 100.0)

    def test_trail_only_ratchets_up(self):
        p = self.pos()
        rules = {"trail_start_r": 1.0, "trail_r": 1.0}
        self.b.update_stop(p, self.bar(104), rules)
        self.assertEqual(p.stop, 102.0)
        self.b.update_stop(p, self.bar(101), rules)  # lower high: stop stays
        self.assertEqual(p.stop, 102.0)
        self.assertEqual(self.b.check_bar(p, day(D, [(103, 103.5, 101.5, 102, 1)])[0])[1], "trail stop")


class RelativeStrengthTests(unittest.TestCase):
    def test_weak_stock_filtered(self):
        c = one_symbol_cfg(filters={"min_rs_pct": 5.0})
        state = new_state(c)
        sym = day(D, RANGE + BREAK)
        ev = Engine(c, state).step(sym[-1].end, {"X": sym}, day(D, INDEX_UP[:4]))
        self.assertEqual(ev[0]["kind"], "FILTER")
        self.assertEqual(state["positions"], {})
