"""Strategies take today's COMPLETED bars for one symbol and return at most one long Signal.

They never see a bar that is still forming, and they never size or place anything.
"""
from .orb import orb
from .vwap_reclaim import vwap_reclaim

REGISTRY = {
    "orb": orb,
    "vwap_reclaim": vwap_reclaim,
}
