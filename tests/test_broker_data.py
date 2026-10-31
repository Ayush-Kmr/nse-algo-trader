import json
import os
import struct
import tempfile
import unittest
from datetime import date, datetime, timedelta

from algo import features, feeds, lab, live, store
from algo.costs import CostModel
from algo.engine import new_state
from algo.models import Bar, Position
from algo.timeutil import IST
from tests.helpers import D, at, cfg, day, flat


class ParsingTests(unittest.TestCase):
    def test_dhan_columns(self):
        t = int(at(D, "09:15").timestamp())
        bars = feeds.dhan_bars({"timestamp": [t], "open": [1], "high": [2], "low": [.5], "close": [1.5], "volume": [10]}, 5)
        self.assertEqual(bars[0].ts, at(D, "09:15"))
        self.assertEqual(bars[0].volume, 10.0)

    def test_dhan_rejects_broken_columns(self):
        with self.assertRaises(ValueError):
            feeds.dhan_bars({"timestamp": [1, 2], "open": [1]}, 5)

    def test_upstox_sorts_and_keeps_ist(self):
        rows = [["2026-10-27T09:20:00+05:30", 2, 3, 1, 2, 5, 0], ["2026-10-27T09:15:00+05:30", 1, 2, 1, 1, 5, 0]]
        bars = feeds.upstox_bars({"data": {"candles": rows}}, 5)
        self.assertEqual(bars[0].ts, at(D, "09:15"))

    def test_windows_respect_the_limit(self):
        w = feeds._windows(date(2026, 1, 1), date(2026, 6, 30), 90)
        self.assertTrue(all((b - a).days < 90 for a, b in w))
        self.assertEqual(w[-1][1], date(2026, 6, 30))

    def test_ticker_packet(self):
        raw = struct.pack("<BHBi", 2, 16, 1, 1333) + struct.pack("<fi", 800.5, 1800000000)
        p = feeds.parse_packet(raw)
        self.assertEqual((p["security_id"], p["ts"]), ("1333", 1800000000))
        self.assertAlmostEqual(p["ltp"], 800.5)

    def test_quote_packet(self):
        raw = struct.pack("<BHBi", 4, 50, 1, 1333) + struct.pack("<fhifiiiffff", 800.5, 10, 1800000000, 799.0, 5000, 1, 2, 790.0, 0.0, 805.0, 788.0)
        p = feeds.parse_packet(raw)
        self.assertEqual(p["volume"], 5000)
        self.assertEqual(p["ts"], 1800000000)

    def test_disconnect_and_junk(self):
        self.assertEqual(feeds.parse_packet(struct.pack("<BHBih", 50, 10, 1, 1, 805)), {"disconnect": 805})
        self.assertIsNone(feeds.parse_packet(b"123"))

    def test_subscribe_batches_of_100(self):
        msgs = feeds.subscribe_messages([str(i) for i in range(250)])
        self.assertEqual([json.loads(m)["InstrumentCount"] for m in msgs], [100, 100, 50])

    def test_missing_token_refuses(self):
        os.environ.pop("DHAN_ACCESS_TOKEN", None)
        with self.assertRaises(RuntimeError):
            feeds.DhanSource()


class ValidationTests(unittest.TestCase):
    def test_finds_problems_and_never_fills_gaps(self):
        bars = day(D, flat(100, 4))
        del bars[2]
        bars[0].high = 90.0
        rep = store.validate("X", bars, 5)
        self.assertEqual(len(rep["bad"]), 1)
        self.assertEqual(len(rep["gaps"]), 1)
        self.assertEqual(len(store.clean(bars, rep)), 2)

    def test_round_trip_keeps_ist_and_metadata(self):
        bars = day(D, flat(100, 3))
        rep = store.validate("X", bars, 5)
        with tempfile.TemporaryDirectory() as tmp:
            path = store.save(tmp, "dhan", "X", bars, 5, rep)
            back = store.load(path, 5)
            meta = json.load(open(path + ".meta.json"))
        self.assertEqual(back[0].ts, bars[0].ts)
        self.assertEqual(meta["source"], "dhan")
        self.assertEqual(meta["timezone"], "Asia/Kolkata")


class FeatureTests(unittest.TestCase):
    def test_no_value_changes_when_future_bars_arrive(self):
        rows = [(100 + i % 7, 101 + i % 7, 99 + i % 7, 100.5 + i % 7, 1000 + i) for i in range(60)]
        full = features.compute(day(D, rows), [], [])
        part = features.compute(day(D, rows[:30]), [], [])
        for k in ("vwap", "ema9", "ema20", "ema50", "rsi", "atr"):
            self.assertAlmostEqual(full[k][29], part[k][29], places=9)

    def test_relative_volume_uses_past_days_only(self):
        past = [day(D, flat(100, 5, 1000))]
        self.assertEqual(features.relative_volume(day(D, flat(100, 3, 2000)), past)[1], 2.0)
        self.assertIsNone(features.relative_volume(day(D, flat(100, 3)), [])[0])


class LabTests(unittest.TestCase):
    def setUp(self):
        self.c = CostModel(cfg()["costs"])

    def test_fills_at_the_next_open_and_stop_beats_target(self):
        rows = [(100, 101, 99, 100, 1), (102, 110, 90, 100, 1), (100, 100, 100, 100, 1)]
        gross, net = lab.exit_trade(day(D, rows), 0, 1, 1.0, 2.0, 3.0, 0.0, self.c)
        self.assertAlmostEqual(gross, 25000 / 102 * -2.0)
        self.assertLess(net, gross)

    def test_short_mirrors(self):
        rows = [(100, 101, 99, 100, 1), (100, 100.2, 96, 97, 1), (97, 97, 97, 97, 1)]
        self.assertGreater(lab.exit_trade(day(D, rows), 0, -1, 1.0, 2.0, 3.0, 0.0, self.c)[0], 0)

    def test_metrics(self):
        t = [(D, 10, 100.0), (D, 10, -50.0), (D + timedelta(days=40), 10, -100.0)]
        m = lab.metrics(t)
        self.assertEqual(m["trades"], 3)
        self.assertEqual(m["pf"], 100 / 150)
        self.assertEqual(m["dd"], 150.0)
        self.assertEqual(len(m["monthly"]), 2)

    def test_reports_when_nothing_qualifies(self):
        rep = {"first": "a", "last": "b", "valid_from": "c", "test_from": "d", "sessions": 1, "rows": []}
        self.assertIn("No reliable trading edge", lab.to_markdown(rep, "yahoo"))


class LiveTests(unittest.TestCase):
    def make(self):
        c = cfg(universe=["X"], strategies=["orb"])
        self.saved = []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.kill = os.path.join(self.tmp.name, "KILL")
        return live.PaperLive(c, new_state(c), {"X": "1", "^NSEI": "13"}, self.saved.append, self.kill)

    def test_bars_build_from_ticks(self):
        b = live.BarBuilder(5)
        self.assertIsNone(b.add("X", 100, at(D, "09:15"), 10))
        self.assertIsNone(b.add("X", 102, at(D, "09:17"), 30))
        done = b.add("X", 101, at(D, "09:20"), 40)
        self.assertEqual((done.open, done.high, done.close, done.volume), (100, 102, 102, 30))

    def test_only_paper_modes_start(self):
        with self.assertRaises(RuntimeError):
            live.PaperLive(cfg(mode="LIVE"), {}, {}, None, "x")

    def test_tick_stop_closes_at_once(self):
        lv = self.make()
        lv.state["date"] = D.isoformat()
        lv.state["positions"]["X"] = Position("X", "orb", 10, 100.0, 98.0, 110.0, at(D, "09:40").isoformat(), 30.0, at(D, "09:40").isoformat()).to_dict()
        lv.on_packet({"security_id": "1", "ltp": 97.5, "ts": int(at(D, "10:00").timestamp()), "volume": 100})
        self.assertEqual(lv.state["positions"], {})
        self.assertEqual(lv.state["today"]["trades"][0]["exit_reason"], "stop")
        self.assertTrue(self.saved)

    def test_bad_ticks_are_dropped(self):
        lv = self.make()
        lv.on_packet({"security_id": "1", "ltp": 0, "ts": int(at(D, "10:00").timestamp()), "volume": 1})
        lv.on_packet({"security_id": "999", "ltp": 10, "ts": int(at(D, "10:00").timestamp()), "volume": 1})
        self.assertIsNone(lv.last_tick)

    def test_stale_feed_alerts_once(self):
        from unittest import mock
        lv = self.make()
        lv.last_tick = at(D, "10:00")
        with mock.patch.object(live, "telegram") as tg:
            self.assertTrue(lv.check_stale(at(D, "10:02")))
            lv.check_stale(at(D, "10:03"))
        tg.assert_called_once()

    def test_kill_file(self):
        lv = self.make()
        self.assertFalse(lv.killed())
        open(self.kill, "w").close()
        self.assertTrue(lv.killed())


class IndexFeedTests(unittest.TestCase):
    def test_index_uses_its_own_segment(self):
        items = json.loads(feeds.subscribe_messages(["1333"], index_ids=("13",))[0])["InstrumentList"]
        self.assertEqual(items[1], {"ExchangeSegment": "IDX_I", "SecurityId": "13"})
