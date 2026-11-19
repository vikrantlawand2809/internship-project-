import math
import statistics
from datetime import date

import pytest

from perfkit import metrics


def test_win_rate_profit_factor_and_expectancy():
    # One win, one loss, and one break-even trade.
    values = [100, -50, 0]
    assert metrics.win_rate_pct(values) == pytest.approx(100 / 3)
    # Profit factor = winning profit / absolute losing profit = 100 / 50.
    assert metrics.profit_factor(values) == 2
    assert metrics.expectancy(values) == pytest.approx(50 / 3)
    assert metrics.win_rate_pct([]) is None


def test_average_and_largest_win_loss():
    values = [100, 50, -20, -40, 0]
    assert metrics.average_win(values) == 75
    assert metrics.average_loss(values) == -30
    assert metrics.largest_win(values) == 100
    assert metrics.largest_loss(values) == -40


def test_profit_factor_when_there_are_no_losses():
    assert metrics.profit_factor([10, 20]) == math.inf
    assert metrics.profit_factor([0]) is None
    assert metrics.profit_factor([-10]) == 0


def test_losing_streak_uses_date_and_id_and_break_even_resets(make_result):
    # By date and ID: A is break-even, then B and C are losses.
    results = [
        make_result(-1, "2026-01-06", "C"),
        make_result(-1, "2026-01-05", "B"),
        make_result(0, "2026-01-05", "A"),
    ]
    assert metrics.longest_losing_streak(results) == 2


def test_equity_curve_and_drawdown(make_result):
    # Starts at 1000, rises to 1100, then falls to 1060.
    results = [
        make_result(100, "2026-01-07", "A", "2026-01-05"),
        make_result(-40, "2026-01-12", "B", "2026-01-08"),
    ]
    curve = metrics.build_equity_curve(results, 1000)
    assert [value for _, value in curve] == [1000, 1000, 1100, 1100, 1100, 1060]
    assert metrics.max_drawdown_pct(curve) == pytest.approx(40 / 1100 * 100)


def test_weekend_exit_moves_to_monday(make_result):
    result = make_result(50, "2026-01-10", "A", "2026-01-09")
    curve = metrics.build_equity_curve([result], 1000)
    assert curve[-1] == (date(2026, 1, 12), 1050)


def test_sharpe_uses_sample_standard_deviation():
    curve = [
        (date(2026, 1, 5), 100.0),
        (date(2026, 1, 6), 110.0),
        (date(2026, 1, 7), 110.0),
    ]
    returns = [0.1, 0.0]
    expected = (
        statistics.mean(returns) /
        statistics.stdev(returns) *
        math.sqrt(252)
    )
    assert metrics.sharpe_ratio(curve) == pytest.approx(expected)


def test_sharpe_is_undefined_for_short_or_flat_curve():
    assert metrics.sharpe_ratio([]) is None
    assert metrics.sharpe_ratio([(date(2026, 1, 5), 100)]) is None
    flat = [(date(2026, 1, 5), 100), (date(2026, 1, 6), 100),
            (date(2026, 1, 7), 100)]
    assert metrics.sharpe_ratio(flat) is None


def test_symbol_table_and_empty_metrics(make_result):
    results = [
        make_result(10, symbol="AAA"),
        make_result(-5, symbol="AAA", trade_id="T2"),
        make_result(20, symbol="BBB", trade_id="T3"),
    ]
    table = metrics.per_symbol_table(results)
    assert table[0]["symbol"] == "AAA"
    assert table[0]["trades"] == 2
    assert table[0]["total_net_pnl"] == 5
    assert table[0]["win_rate_pct"] == 50

    empty = metrics.compute_metrics([])
    assert empty.total_trades == 0
    assert empty.total_net_pnl == 0
    assert empty.ending_equity == metrics.DEFAULT_CAPITAL
    assert empty.sharpe_ratio is None


def test_all_winners_and_single_trade(make_result):
    winner = make_result(10)
    result = metrics.compute_metrics([winner], 1000)
    assert result.profit_factor == math.inf
    assert result.average_loss is None
    assert result.total_trades == 1


def test_one_day_curve_and_all_winning_trades(make_result):
    results = [
        make_result(10, "2026-01-05", "A"),
        make_result(20, "2026-01-05", "B"),
    ]
    curve = metrics.build_equity_curve(results, 1000)
    result = metrics.compute_metrics(results, 1000)
    assert len(curve) == 1
    assert result.ending_equity == 1030
    assert result.profit_factor == math.inf
    assert result.sharpe_ratio is None
