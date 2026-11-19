from contextlib import contextmanager
from typing import Iterable, Iterator

import backtesting
from backtesting.backtesting import Position, Trade


SUPPORTED_VERSION = "0.6.2"
_ORIGINAL_PL_PCT = Position.pl_pct


def position_pl_pct(trades: Iterable[Trade]) -> float:
    """Total cash P&L divided by the money used to open the trades."""
    total_profit = 0.0
    total_cost = 0.0

    for trade in trades:
        total_profit += trade.pl
        # Use shares multiplied by their own entry price as the weight.
        total_cost += abs(trade.size) * trade.entry_price

    # No open trades means there is no position return.
    return total_profit / total_cost if total_cost else 0.0


def _fixed_property(position: Position) -> float:
    # backtesting.py 0.6.2 keeps open trades in this private broker field.
    trades = position._Position__broker.trades
    return position_pl_pct(trades)


def _check_version() -> None:
    if backtesting.__version__ != SUPPORTED_VERSION:
        raise RuntimeError(
            "This fix is for backtesting==0.6.2, but version " +
            backtesting.__version__ + " is installed"
        )


@contextmanager
def patched_pl_pct() -> Iterator[None]:
    """Temporarily fix Position.pl_pct, then restore the original property."""
    _check_version()
    Position.pl_pct = property(_fixed_property)
    try:
        yield
    finally:
        Position.pl_pct = _ORIGINAL_PL_PCT
