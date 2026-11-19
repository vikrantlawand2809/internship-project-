import json
import math
from pathlib import Path
from typing import Dict, Union

from perfkit.calculations import calculate_trades
from perfkit.loader import load_trades
from perfkit.metrics import (
    DEFAULT_CAPITAL,
    build_equity_curve,
    compute_metrics,
    per_symbol_table,
)


def build_report(
    csv_path: Union[str, Path],
    starting_capital: float = DEFAULT_CAPITAL,
) -> Dict[str, object]:
    """Read CSV -> calculate trades -> calculate metrics -> combine output."""
    loaded = load_trades(csv_path)
    results = calculate_trades(loaded.trades)
    metrics = compute_metrics(results, starting_capital)
    curve = build_equity_curve(results, starting_capital)

    # Both text and JSON output use this same report dictionary.
    return {
        "input_file": str(csv_path),
        "starting_capital": starting_capital,
        "valid_trades": len(loaded.trades),
        "rejected_trades": len(loaded.rejections),
        "metrics": metrics.to_dict(),
        "per_symbol": per_symbol_table(results),
        "equity_curve": [
            {"date": day.isoformat(), "equity": value}
            for day, value in curve
        ],
        "rejected": [
            {"trade_id": item.trade_id, "line": item.line,
             "reason": item.reason}
            for item in loaded.rejections
        ],
    }


def to_json(report: Dict[str, object]) -> str:
    """Convert the report to valid indented JSON."""
    safe_report = dict(report)
    metrics = dict(report["metrics"])

    # JSON does not support infinity. Show it as the text "inf".
    if metrics["profit_factor"] == math.inf:
        metrics["profit_factor"] = "inf"
    safe_report["metrics"] = metrics
    return json.dumps(safe_report, indent=2)


def _money(value):
    return "n/a" if value is None else "INR " + format_inr(value)


def format_inr(value: float) -> str:
    """Format an amount using Indian digit grouping."""
    amount = f"{abs(value):.2f}"
    whole, decimals = amount.split(".")
    groups = [whole[-3:]]
    remaining = whole[:-3]
    while remaining:
        groups.append(remaining[-2:])
        remaining = remaining[:-2]
    whole = ",".join(reversed(groups))
    sign = "-" if value < 0 else ""
    return sign + whole + "." + decimals


def _percent(value, digits=2):
    return "n/a" if value is None else f"{value:.{digits}f} %"


def _format_metrics(metrics: Dict[str, object]):
    return [
        f"Total net P&L:          {_money(metrics['total_net_pnl'])}",
        f"Ending equity:          {_money(metrics['ending_equity'])}",
        "Win rate:               "
        f"{_percent(metrics['win_rate_pct'])} "
        f"({metrics['winning_trades']} wins / "
        f"{metrics['losing_trades']} losses)",
        "Profit factor:          "
        f"{_metric_number(metrics['profit_factor'], 4)}",
        f"Expectancy:             {_money(metrics['expectancy'])}",
        f"Average win:            {_money(metrics['average_win'])}",
        f"Average loss:           {_money(metrics['average_loss'])}",
        f"Largest win:            {_money(metrics['largest_win'])}",
        f"Largest loss:           {_money(metrics['largest_loss'])}",
        f"Longest losing streak:  {metrics['longest_losing_streak']}",
        "Max drawdown:           "
        f"{_percent(metrics['max_drawdown_pct'], 4)}",
        "Sharpe ratio:           "
        f"{_metric_number(metrics['sharpe_ratio'], 4)}",
    ]


def _format_symbol_rows(rows):
    if not rows:
        return ["(no valid trades)"]

    return [
        f"{row['symbol']}  {row['trades']} trades  "
        f"{_money(row['total_net_pnl'])}  {_percent(row['win_rate_pct'])}"
        for row in rows
    ]


def _format_rejected_rows(rows):
    if not rows:
        return ["(none)"]

    return [
        f"line {row['line']}  {row['trade_id']}  {row['reason']}"
        for row in rows
    ]


def format_text_report(report: Dict[str, object]) -> str:
    """Format the report so it is readable in a terminal."""
    lines = [
        "PERFKIT PERFORMANCE REPORT",
        "=" * 50,
        f"File:             {report['input_file']}",
        f"Starting capital: {_money(report['starting_capital'])}",
        f"Trades:           {report['valid_trades']} valid, "
        f"{report['rejected_trades']} rejected",
        "",
        "METRICS",
        "-" * 50,
    ]
    lines.extend(_format_metrics(report["metrics"]))
    lines.extend(["", "PER-SYMBOL PERFORMANCE", "-" * 50])
    lines.extend(_format_symbol_rows(report["per_symbol"]))
    lines.extend(["", "REJECTED ROWS", "-" * 50])
    lines.extend(_format_rejected_rows(report["rejected"]))
    return "\n".join(lines)


def _metric_number(value, digits):
    if value is None:
        return "n/a"
    if math.isinf(value):
        return "inf (no losing trades)"
    return f"{value:.{digits}f}"
