from datetime import date

from perfkit.calculations import calculate_trade
from perfkit.loader import Trade


def make_trade(side, entry, exit_price, fees=0):
    return Trade(
        "T1", "ABC", side, 2, entry, exit_price,
        date(2026, 1, 1), date(2026, 1, 2), fees,
    )


def test_long_winner():
    result = calculate_trade(make_trade("LONG", 10, 15, fees=2))
    assert result.gross_pnl == 10
    assert result.net_pnl == 8


def test_long_loser():
    result = calculate_trade(make_trade("LONG", 15, 10, fees=2))
    assert result.gross_pnl == -10
    assert result.net_pnl == -12


def test_short_winner():
    result = calculate_trade(make_trade("SHORT", 15, 10, fees=2))
    assert result.gross_pnl == 10
    assert result.net_pnl == 8


def test_short_loser():
    result = calculate_trade(make_trade("SHORT", 10, 15, fees=2))
    assert result.gross_pnl == -10
    assert result.net_pnl == -12


def test_return_percentage():
    result = calculate_trade(make_trade("LONG", 10, 15))
    assert result.return_pct == 50
