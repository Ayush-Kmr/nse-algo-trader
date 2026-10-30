"""Strategies take today's COMPLETED bars for one symbol and return at most one long Signal.

They never see a bar that is still forming, and they never size or place anything.
"""
from .afternoon_high import afternoon_high
from .orb import orb
from .pullback import pullback
from .vwap_reclaim import vwap_reclaim
from .vwap_revert import vwap_revert

REGISTRY = {
    "orb": orb,
    "vwap_reclaim": vwap_reclaim,
    "pullback": pullback,
    "vwap_revert": vwap_revert,
    "afternoon_high": afternoon_high,
}
