import csv
from datetime import date

import pytest

from perfkit.calculations import TradeResult
from perfkit.loader import Trade


@pytest.fixture
def write_trades_csv(tmp_path):
    """Write a small CSV file and return its path."""
    columns = (
        "trade_id",
        "symbol",
        "side",
        "quantity",
        "entry_price",
        "exit_price",
        "entry_date",
        "exit_date",
        "fees",
    )

    def write(filename, rows=(), header=columns):
        path = tmp_path / filename
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if header is not None:
                writer.writerow(header)
            writer.writerows(rows)
        return path

    return write


# Pytest makes this small trade builder available to all metric tests.
@pytest.fixture
def make_result():
    """Make a small example trade for metric tests."""
    def create(net, exit_day="2026-01-05", trade_id="T1",
               entry_day=None, symbol="AAA"):
        if entry_day is None:
            entry_day = exit_day
        entry_date = date.fromisoformat(entry_day)
        exit_date = date.fromisoformat(exit_day)
        trade = Trade(
            trade_id=trade_id,
            symbol=symbol,
            side="LONG",
            quantity=1,
            entry_price=100,
            exit_price=100 + net,
            entry_date=entry_date,
            exit_date=exit_date,
            fees=0,
        )
        return TradeResult(trade, net, net, net)
    return create
