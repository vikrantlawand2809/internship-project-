from dataclasses import dataclass
from typing import Iterable, List

from perfkit.loader import Trade


@dataclass(frozen=True)
class TradeResult:
    """A trade and its calculated values."""

    trade: Trade
    gross_pnl: float
    net_pnl: float
    return_pct: float


def calculate_trade(trade: Trade) -> TradeResult:
    """Return gross profit, net profit after fees, and percentage return."""
    if trade.side == "LONG":
        # A long trade earns money when the exit price is higher.
        gross = (trade.exit_price - trade.entry_price) * trade.quantity
    else:
        # A short trade earns money when the exit price is lower.
        gross = (trade.entry_price - trade.exit_price) * trade.quantity

    net = round(gross - trade.fees, 6)
    cost = trade.entry_price * trade.quantity
    # Return is measured against the money used to open the trade.
    return TradeResult(trade, round(gross, 6), net, net / cost * 100)


def calculate_trades(trades: Iterable[Trade]) -> List[TradeResult]:
    """Calculate results for each trade in the same order."""
    return [calculate_trade(trade) for trade in trades]
