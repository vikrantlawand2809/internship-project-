import argparse
import math
import sys
from typing import List, Optional

from perfkit.metrics import DEFAULT_CAPITAL
from perfkit.report import build_report, format_text_report, to_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trade performance report.")
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report", help="report on a trade CSV")
    report.add_argument("csv_file", help="path to the CSV file")
    report.add_argument("--format", choices=("text", "json"), default="text")
    report.add_argument("--capital", type=float, default=DEFAULT_CAPITAL)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run perfkit and return an exit code."""
    # argparse reads the user's command and checks its options.
    args = _parser().parse_args(argv)
    if not math.isfinite(args.capital) or args.capital <= 0:
        print("Error: capital must be a positive number", file=sys.stderr)
        return 1

    try:
        report = build_report(args.csv_file, args.capital)
    except (OSError, ValueError) as error:
        print("Error:", error, file=sys.stderr)
        return 1

    if args.format == "json":
        print(to_json(report))
    else:
        print(format_text_report(report))
    return 0
