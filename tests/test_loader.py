from datetime import date

from perfkit.loader import load_trades


def test_supplied_csv_has_expected_rows():
    loaded = load_trades("trades.csv")
    assert len(loaded.trades) == 61
    assert len(loaded.rejections) == 5


def test_both_date_formats_and_lowercase_side(write_trades_csv):
    path = write_trades_csv(
        "trades.csv",
        [[
            "1", "ABC", "long", "2", "10", "12",
            "05/01/2026", "2026-01-06", "1",
        ]],
    )
    trade = load_trades(path).trades[0]
    assert trade.side == "LONG"
    assert trade.entry_date == date(2026, 1, 5)


def test_bad_row_is_rejected_but_next_row_is_read(write_trades_csv):
    path = write_trades_csv(
        "trades.csv",
        [
            [
                "bad", "ABC", "BUY", "1", "10", "11",
                "2026-01-01", "2026-01-02", "0",
            ],
            [
                "good", "ABC", "LONG", "1", "10", "11",
                "2026-01-01", "2026-01-02", "0",
            ],
        ],
    )
    loaded = load_trades(path)
    assert len(loaded.trades) == 1
    assert loaded.rejections[0].trade_id == "bad"
    assert "side" in loaded.rejections[0].reason


def test_exact_duplicate_is_rejected(write_trades_csv):
    row = [
        "1", "ABC", "LONG", "1", "10", "11",
        "2026-01-01", "2026-01-02", "0",
    ]
    path = write_trades_csv("trades.csv", [row, row])
    loaded = load_trades(path)
    assert len(loaded.trades) == 1
    assert "duplicate" in loaded.rejections[0].reason


def test_empty_file_returns_empty_lists(write_trades_csv):
    path = write_trades_csv("empty.csv", header=None)
    loaded = load_trades(path)
    assert loaded.trades == []
    assert loaded.rejections == []


def test_missing_columns_has_clear_error(write_trades_csv):
    path = write_trades_csv("wrong.csv", header=["trade_id", "symbol"])
    try:
        load_trades(path)
    except ValueError as error:
        assert "Missing required column" in str(error)
    else:
        raise AssertionError("Expected missing-column error")
