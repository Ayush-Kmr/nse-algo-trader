import unittest

from algo.costs import CostModel
from algo.models import round_tick
from algo.sizing import size_position
from tests.helpers import cfg


class CostTests(unittest.TestCase):
    def setUp(self):
        self.c = CostModel(cfg()["costs"])

    def test_design_doc_example_is_about_56(self):
        # docs/UNATTENDED_DESIGN.md: 50 shares, buy 500, stop 495 -> about ₹56 round trip.
        ch = self.c.round_trip(25000, 24750)
        self.assertEqual(ch.brokerage, 40.0)
        self.assertAlmostEqual(ch.stt, 6.19, places=2)
        self.assertAlmostEqual(ch.stamp, 0.75, places=2)
        self.assertAlmostEqual(ch.total, 55.94, delta=0.05)

    def test_small_order_pays_percentage_not_flat(self):
        self.assertEqual(float(self.c.brokerage(5000)), 5.0)   # 0.1% of 5,000 < ₹20
        self.assertEqual(float(self.c.brokerage(50000)), 20.0)

    def test_stt_only_on_sell_stamp_only_on_buy(self):
        self.assertEqual(self.c.round_trip(10000, 0).stt, 0.0)
        self.assertEqual(self.c.round_trip(0, 10000).stamp, 0.0)


class SizingTests(unittest.TestCase):
    def setUp(self):
        self.c = CostModel(cfg()["costs"])

    def test_all_in_loss_fits_budget(self):
        s = size_position(500, 495, 250, self.c, 0.05, 40000)
        self.assertGreater(s.qty, 0)
        self.assertLessEqual(s.loss_at_stop, 250)
        # Without costs it would be 250/5.5 = 45; costs must shave it.
        self.assertLess(s.qty, 46)

    def test_position_cap_binds(self):
        s = size_position(500, 499, 250, self.c, 0.05, 10000)
        self.assertLessEqual(s.qty * s.buy_px, 10000)
        self.assertEqual(s.limited_by, "position cap / cash")

    def test_stop_too_far(self):
        self.assertEqual(size_position(500, 200, 250, self.c, 0.05, 40000).qty, 0)

    def test_invalid_stop(self):
        self.assertEqual(size_position(500, 510, 250, self.c, 0.05, 40000).qty, 0)


class TickTests(unittest.TestCase):
    def test_round_tick(self):
        self.assertEqual(round_tick(100.03, 0.05, "down"), 100.0)
        self.assertEqual(round_tick(100.03, 0.05, "up"), 100.05)
        self.assertEqual(round_tick(100.05, 0.05, "down"), 100.05)
        self.assertEqual(round_tick(100.05, 0.05, "up"), 100.05)


if __name__ == "__main__":
    unittest.main()
