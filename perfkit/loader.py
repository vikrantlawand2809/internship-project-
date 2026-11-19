import csv
import math
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import List, Union


REQUIRED_COLUMNS = (
    "trade_id", "symbol", "side", "quantity", "entry_price",
    "exit_price", "entry_date", "exit_date", "fees",
)


class MissingColumnsError(ValueError):
    """Raised when the CSV header is missing required columns."""


@dataclass(frozen=True)
class Trade:
    """A valid trade with cleaned values."""

    trade_id: str
    symbol: str
    side: str
    quantity: int
    entry_price: float
    exit_price: float
    entry_date: date
    exit_date: date
    fees: float


@dataclass(frozen=True)
class Rejection:
    """A row that could not be used, with its CSV line and reason."""

    trade_id: str
    reason: str
    line: int


@dataclass
class LoadResult:
    """Valid trades and rejected CSV rows."""

    trades: List[Trade] = field(default_factory=list)
    rejections: List[Rejection] = field(default_factory=list)


def _number(text: str, name: str) -> float:
    if not text:
        raise ValueError(f"{name} is missing")
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"{name} is not numeric") from None
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def _date(text: str, name: str) -> date:
    if not text:
        raise ValueError(f"{name} is missing")
    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            pass
    raise ValueError(f"{name} must be YYYY-MM-DD or DD/MM/YYYY")


def _make_trade(row: dict) -> Trade:
    side = row["side"].upper()
    if side not in ("LONG", "SHORT"):
        raise ValueError("side must be LONG or SHORT")

    quantity = _number(row["quantity"], "quantity")
    if quantity <= 0 or not quantity.is_integer():
        raise ValueError("quantity must be a positive whole number")

    entry_price = _number(row["entry_price"], "entry_price")
    exit_price = _number(row["exit_price"], "exit_price")
    fees = _number(row["fees"], "fees")
    if entry_price <= 0 or exit_price <= 0:
        raise ValueError("prices must be positive")

    entry_date = _date(row["entry_date"], "entry_date")
    exit_date = _date(row["exit_date"], "exit_date")
    if exit_date < entry_date:
        raise ValueError("exit_date is before entry_date")

    return Trade(
        trade_id=row["trade_id"],
        symbol=row["symbol"],
        side=side,
        quantity=int(quantity),
        entry_price=entry_price,
        exit_price=exit_price,
        entry_date=entry_date,
        exit_date=exit_date,
        fees=fees,
    )


def load_trades(path: Union[str, Path]) -> LoadResult:
    """Load trades, skipping invalid rows and explaining each rejection."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    result = LoadResult()
    seen_rows = {}

    try:
        with file_path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            # Lowercase headers so "Trade_ID" and "trade_id" both work.
            headers = [
                (name or "").strip().lower()
                for name in (reader.fieldnames or [])
            ]
            if not headers:
                return result

            missing = [name for name in REQUIRED_COLUMNS if name not in headers]
            if missing:
                raise MissingColumnsError(
                    f"Missing required column(s): {', '.join(missing)}"
                )
            reader.fieldnames = headers

            for row in reader:
                line = reader.line_num
                cleaned = {
                    name: (row.get(name) or "").strip()
                    for name in REQUIRED_COLUMNS
                }
                trade_id = cleaned["trade_id"] or f"<line {line}>"

                # Compare all required cells to find exact duplicate rows.
                if None in row:
                    result.rejections.append(
                        Rejection(trade_id, "row has extra values", line)
                    )
                    continue

                row_key = tuple(cleaned[name] for name in REQUIRED_COLUMNS)
                if row_key in seen_rows:
                    first_line = seen_rows[row_key]
                    result.rejections.append(
                        Rejection(
                            trade_id,
                            f"exact duplicate of line {first_line}",
                            line,
                        )
                    )
                    continue
                seen_rows[row_key] = line

                try:
                    result.trades.append(_make_trade(cleaned))
                except ValueError as error:
                    # Reject this row, then continue reading the next one.
                    result.rejections.append(
                        Rejection(trade_id, str(error), line)
                    )
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(
            f"Could not read {file_path} as a UTF-8 CSV: {error}"
        ) from error

    return result
