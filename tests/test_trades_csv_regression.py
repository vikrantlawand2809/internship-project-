from pathlib import Path

import pytest

from perfkit.report import build_report


@pytest.fixture
def report():
    return build_report(Path("trades.csv"))


def test_supplied_csv_row_counts(report):
    assert report["valid_trades"] == 61
    assert report["rejected_trades"] == 5


def test_supplied_csv_metrics(report):
    metrics = report["metrics"]
    assert metrics["total_net_pnl"] == pytest.approx(6182.02)
    assert metrics["win_rate_pct"] == pytest.approx(63.934426)
    assert metrics["profit_factor"] == pytest.approx(1.438888)
    assert metrics["expectancy"] == pytest.approx(101.34459)
    assert metrics["average_win"] == pytest.approx(519.68359)
    assert metrics["average_loss"] == pytest.approx(-640.256364)
    assert metrics["largest_win"] == 2506.57
    assert metrics["largest_loss"] == -2819.21
    assert metrics["longest_losing_streak"] == 5
    assert metrics["max_drawdown_pct"] == pytest.approx(0.60142)
    assert metrics["sharpe_ratio"] == pytest.approx(1.496614)


def test_supplied_csv_per_symbol_and_equity_curve(report):
    assert len(report["per_symbol"]) == 5
    assert report["equity_curve"][0]["date"] == "2026-01-07"
    assert report["equity_curve"][-1]["equity"] == pytest.approx(1006182.02)
