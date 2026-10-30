import unittest

from algo.costs import CostModel
from algo.models import Signal
from algo.risk import Account, check_entry
from tests.helpers import D, at, cfg


def acct(**kw):
    base = dict(equity=50000, cash_available=50000, open_positions=0, open_risk=0, trades_today=0,
                realised_today=0.0)
    base.update(kw)
    return Account(**base)


SIG = Signal("SBIN", "orb", 800.0, 795.0, 818.0, at(D, "09:35"), "test")


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg()
        self.c = CostModel(self.cfg["costs"])

    def check(self, sig=SIG, a=None, hm="10:00"):
        return check_entry(sig, a or acct(), self.cfg, self.c, at(D, hm))

    def test_good_trade_passes(self):
        v = self.check()
        self.assertTrue(v.ok, v.reasons)
        self.assertGreater(v.qty, 0)
        self.assertLessEqual(v.details["loss_at_stop"], 250)

    def test_outside_window(self):
        self.assertIn("outside entry window", self.check(hm="15:00").reasons[0])

    def test_kill_switch(self):
        self.assertFalse(self.check(a=acct(kill_switch=True)).ok)

    def test_daily_limit_exhausted(self):
        v = self.check(a=acct(realised_today=-500))
        self.assertFalse(v.ok)
        self.assertIn("daily loss limit", v.reasons[-1])

    def test_daily_limit_shrinks_budget(self):
        v = self.check(a=acct(realised_today=-270))  # ₹230 room left of ₹500
        self.assertTrue(v.ok, v.reasons)
        self.assertLessEqual(v.details["loss_at_stop"], 230)

    def test_max_positions(self):
        self.assertFalse(self.check(a=acct(open_positions=2)).ok)

    def test_same_symbol_twice(self):
        self.assertFalse(self.check(a=acct(symbols_today={"SBIN"})).ok)

    def test_bad_geometry(self):
        bad = Signal("SBIN", "orb", 800.0, 805.0, 812.0, at(D, "09:35"), "test")
        self.assertIn("bad geometry", self.check(sig=bad).reasons[0])

    def test_reward_too_small_after_costs(self):
        thin = Signal("SBIN", "orb", 800.0, 795.0, 803.0, at(D, "09:35"), "test")
        v = self.check(sig=thin)
        self.assertFalse(v.ok)
        self.assertTrue(any("reward:risk" in r for r in v.reasons))

    def test_no_leverage(self):
        v = self.check(a=acct(cash_available=500))
        self.assertFalse(v.ok)


if __name__ == "__main__":
    unittest.main()
