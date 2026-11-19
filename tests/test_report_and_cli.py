import json

from perfkit.cli import main
from perfkit.report import build_report, format_inr, format_text_report, to_json


def test_report_and_json_have_same_metrics(write_trades_csv):
    path = write_trades_csv(
        "trades.csv",
        [[
            "1", "ABC", "LONG", "1", "10", "12",
            "2026-01-05", "2026-01-06", "0",
        ]],
    )
    report = build_report(path, 1000)
    assert report["metrics"]["total_net_pnl"] == 2
    assert json.loads(to_json(report))["valid_trades"] == 1
    assert "PERFKIT PERFORMANCE REPORT" in format_text_report(report)


def test_json_represents_infinite_profit_factor_as_text(write_trades_csv):
    path = write_trades_csv(
        "winners.csv",
        [[
            "1", "ABC", "LONG", "1", "10", "12",
            "2026-01-05", "2026-01-06", "0",
        ]],
    )
    report = build_report(path)
    assert json.loads(to_json(report))["metrics"]["profit_factor"] == "inf"


def test_empty_csv_and_cli_errors(tmp_path, capsys, write_trades_csv):
    empty = write_trades_csv("empty.csv", header=None)
    report = build_report(empty)
    assert report["valid_trades"] == 0
    assert report["metrics"]["ending_equity"] == 1_000_000

    missing = tmp_path / "missing.csv"
    assert main(["report", str(missing)]) == 1
    assert "File not found" in capsys.readouterr().err


def test_cli_wrong_columns_reports_error(write_trades_csv, capsys):
    path = write_trades_csv("wrong.csv", header=["trade_id", "symbol"])
    assert main(["report", str(path)]) == 1
    assert "Missing required column" in capsys.readouterr().err


def test_cli_prints_a_report(write_trades_csv, capsys):
    path = write_trades_csv("trades.csv")
    assert main(["report", str(path)]) == 0
    assert "PERFKIT PERFORMANCE REPORT" in capsys.readouterr().out


def test_format_inr_uses_indian_digit_grouping():
    assert format_inr(1234567.89) == "12,34,567.89"
    assert format_inr(-1234.5) == "-1,234.50"
