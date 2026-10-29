import unittest

from algo.strategies.orb import orb
from algo.strategies.vwap_reclaim import vwap_reclaim
from tests.helpers import D, cfg, day, flat

# Opening range 09:15-09:30: high 102, low 100 (2% wide).
RANGE = [(100, 102, 100, 101, 5000), (101, 101.5, 100.2, 101, 2000), (101, 101.8, 100.5, 101.2, 2000)]


class OrbTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg()

    def test_first_close_above_range(self):
        bars = day(D, RANGE + [(101.2, 102.4, 101, 101.9, 3000), (101.9, 103, 101.8, 102.6, 3000)])
        s = orb("X", bars, self.cfg)
        self.assertIsNotNone(s)
        self.assertEqual(s.bar_ts.strftime("%H:%M"), "09:35")  # the wick at 09:30 does not count
        self.assertEqual(s.entry, 102.6)
        self.assertEqual(s.stop, 101.0)                           # range midpoint
        self.assertAlmostEqual(s.target, 102.6 + 3 * 1.6, places=2)

    def test_range_not_complete(self):
        self.assertIsNone(orb("X", day(D, RANGE[:2]), self.cfg))

    def test_missing_open_bar(self):
        self.assertIsNone(orb("X", day(D, RANGE + [(102, 104, 102, 103.5, 9000)], start="09:20"), self.cfg))

    def test_range_too_wide(self):
        wide = [(100, 106, 100, 103, 5000)] + RANGE[1:]
        self.assertIsNone(orb("X", day(D, wide + [(103, 107, 103, 106.5, 9000)]), self.cfg))

    def test_weak_volume_kills_the_day(self):
        bars = day(D, RANGE + [(101.2, 103, 101, 102.6, 100), (102.6, 104, 102.5, 103.8, 9000)])
        self.assertIsNone(orb("X", bars, self.cfg))


class VwapTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg()

    def test_reclaim_after_10(self):
        rows = [(100, 101, 99.8, 100.8, 4000)] + flat(100.6, 7, 2000)   # through 09:50
        rows += [(100.6, 100.6, 99.9, 100.2, 2000)]                         # 09:55 dips below VWAP
        rows += [(100.2, 100.3, 99.6, 99.9, 2000)]                          # 10:00 still below
        rows += [(99.9, 101.6, 99.9, 101.5, 6000)]                          # 10:05 reclaims, above open
        s = vwap_reclaim("X", day(D, rows), self.cfg)
        self.assertIsNotNone(s)
        self.assertEqual(s.bar_ts.strftime("%H:%M"), "10:05")
        self.assertEqual(s.stop, 99.6)
        self.assertGreater(s.target, s.entry)

    def test_needs_green_day(self):
        rows = [(102, 102.5, 99.8, 100.8, 4000)] + flat(100.6, 7, 2000)
        rows += [(100.6, 100.6, 99.9, 100.2, 2000), (100.2, 100.3, 99.6, 99.9, 2000),
                 (99.9, 101.6, 99.9, 101.5, 6000)]  # 101.5 < day open 102
        self.assertIsNone(vwap_reclaim("X", day(D, rows), self.cfg))


if __name__ == "__main__":
    unittest.main()
