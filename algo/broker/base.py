"""What the engine needs from a broker. PaperBroker implements it; AngelOneBroker does not yet.

The shape assumes instant fills, which is true only on paper. A live broker also needs asynchronous
order state, partial fills and reconciliation: see docs/ARCHITECTURE.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple

from ..models import Bar, Position, Signal, Trade


class Broker(ABC):
    @abstractmethod
    def open(self, sig: Signal, qty: int, planned_risk: float) -> Position:
        """Enter a position for an approved signal."""

    @abstractmethod
    def check_bar(self, pos: Position, bar: Bar) -> Optional[Tuple[float, str]]:
        """-> (exit price, reason) if this completed bar exits the position."""

    @abstractmethod
    def update_stop(self, pos: Position, bar: Bar, rules: dict) -> None:
        """Ratchet the stop after a completed bar with no exit."""

    @abstractmethod
    def square_off_price(self, last_price: float) -> float:
        """The price a forced exit gets."""

    @abstractmethod
    def close(self, pos: Position, price: float, reason: str, ts: datetime) -> Trade:
        """Exit the position and return the charged trade."""
