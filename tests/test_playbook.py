import unittest
from datetime import datetime, timedelta

from algo import playbook
from algo.models import Bar
from algo.timeutil import IST


def bar(minute, o, h, l, c):
    return Bar(datetime(2026, 10, 1, 9, 15, tzinfo=IST) + timedelta(minutes=minute), o, h, l, c, 1000.0)


class Walk(unittest.TestCase):
    def test_stop_beats_target_in_one_bar(self):
        self.assertEqual(playbook.walk([bar(30, 100, 111, 94, 100)], 100, 95, 110), (95, "stop"))

    def test_gap_through_stop_fills_at_the_open(self):
        self.assertEqual(playbook.walk([bar(30, 90, 91, 89, 90)], 100, 95, 110), (90, "stop"))

    def test_flat_at_1515(self):
        self.assertEqual(playbook.walk([bar(360, 102, 103, 101, 102)], 100, 95, 110), (102, "close"))


class Setups(unittest.TestCase):
    def test_breakout_needs_a_close_above_the_last_twenty(self):
        c = [100.0] * 30 + [101.0]
        self.assertIn("breakout_20d", playbook.setups_at(c, playbook.rsi_series(c), 30))

    def test_wilder_rsi_matches_a_one_way_market(self):
        c = [float(x) for x in range(1, 20)]
        self.assertEqual(playbook.rsi_series(c)[-1], 100.0)
        self.assertLess(playbook.rsi_series(c[::-1])[-1], 1.0)


class LowerBound(unittest.TestCase):
    def test_uses_daily_totals(self):
        d1, d2 = datetime(2026, 1, 1).date(), datetime(2026, 1, 2).date()
        trades = [(d1, 0, 10.0), (d1, 0, 10.0), (d2, 0, -10.0), (d2, 0, -10.0)]
        self.assertLess(playbook.lower_bound(trades, 2.0), 0)


if __name__ == "__main__":
    unittest.main()
