"""Calculate portfolio performance metrics from completed trades."""

import math
import statistics
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from perfkit.calculations import TradeResult


DEFAULT_CAPITAL = 1_000_000


def win_rate_pct(nets: Sequence[float]) -> Optional[float]:
    """Winning trades divided by all trades, as a percentage."""
    if not nets:
        return None
    wins = sum(value > 0 for value in nets)
    return round(wins / len(nets) * 100, 6)


def profit_factor(nets: Sequence[float]) -> Optional[float]:
    """Total winning profit divided by the absolute total losing profit."""
    total_wins = sum(value for value in nets if value > 0)
    total_losses = sum(value for value in nets if value < 0)

    if total_losses:
        return round(total_wins / abs(total_losses), 6)
    if total_wins:
        return math.inf
    return None


def expectancy(nets: Sequence[float]) -> Optional[float]:
    """Average net profit per trade."""
    return round(sum(nets) / len(nets), 6) if nets else None


def average_win(nets: Sequence[float]) -> Optional[float]:
    wins = [value for value in nets if value > 0]
    return round(sum(wins) / len(wins), 6) if wins else None


def average_loss(nets: Sequence[float]) -> Optional[float]:
    losses = [value for value in nets if value < 0]
    return round(sum(losses) / len(losses), 6) if losses else None


def largest_win(nets: Sequence[float]) -> Optional[float]:
    wins = [value for value in nets if value > 0]
    return max(wins) if wins else None


def largest_loss(nets: Sequence[float]) -> Optional[float]:
    losses = [value for value in nets if value < 0]
    return min(losses) if losses else None


def longest_losing_streak(results: Sequence[TradeResult]) -> int:
    # The required order is exit date, then trade ID.
    ordered = sorted(
        results, key=lambda result: (
            result.trade.exit_date, result.trade.trade_id
        )
    )
    current = longest = 0
    for result in ordered:
        if result.net_pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            # A win or break-even trade starts a new streak.
            current = 0
    return longest


def _next_weekday(day: date) -> date:
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def build_equity_curve(
    results: Sequence[TradeResult],
    starting_capital: float = DEFAULT_CAPITAL,
) -> List[Tuple[date, float]]:
    """Build daily equity from first entry date through last exit date."""
    if not results:
        return []

    first = _next_weekday(min(result.trade.entry_date for result in results))
    last = _next_weekday(max(result.trade.exit_date for result in results))
    daily_profit: Dict[date, float] = {}

    day = first
    while day <= last:
        if day.weekday() < 5:
            daily_profit[day] = 0.0
        day += timedelta(days=1)

    for result in results:
        # A weekend exit is moved to Monday so its profit is included.
        exit_day = _next_weekday(result.trade.exit_date)
        daily_profit[exit_day] += result.net_pnl

    equity = starting_capital
    curve = []
    for day in sorted(daily_profit):
        equity = round(equity + daily_profit[day], 6)
        curve.append((day, equity))
    return curve


def max_drawdown_pct(curve: Sequence[Tuple[date, float]]) -> float:
    """Return the largest drop from an earlier equity-curve peak."""
    if not curve:
        return 0.0
    peak_equity = curve[0][1]
    largest_drawdown = 0.0
    for _, equity in curve:
        peak_equity = max(peak_equity, equity)
        if peak_equity:
            drawdown = (peak_equity - equity) / peak_equity * 100
            largest_drawdown = max(largest_drawdown, drawdown)
    return round(largest_drawdown, 6)


def sharpe_ratio(curve: Sequence[Tuple[date, float]]) -> Optional[float]:
    """Annualized Sharpe ratio using sample standard deviation and 252 days."""
    values = [equity for _, equity in curve]
    returns = [
        current / previous - 1
        for previous, current in zip(values, values[1:])
        if previous != 0
    ]
    if len(returns) < 2:
        return None
    # statistics.stdev uses the sample standard deviation (ddof=1).
    deviation = statistics.stdev(returns)
    if deviation == 0:
        return None
    return round(statistics.mean(returns) / deviation * math.sqrt(252), 6)


def per_symbol_table(results: Sequence[TradeResult]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[float]] = {}
    for result in results:
        symbol = result.trade.symbol
        if symbol not in grouped:
            grouped[symbol] = []
        grouped[symbol].append(result.net_pnl)

    table = []
    for symbol in sorted(grouped):
        values = grouped[symbol]
        table.append({
            "symbol": symbol,
            "trades": len(values),
            "total_net_pnl": round(sum(values), 6),
            "win_rate_pct": win_rate_pct(values) or 0.0,
        })
    return table


@dataclass(frozen=True)
class PerformanceMetrics:
    starting_capital: float
    ending_equity: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_net_pnl: float
    win_rate_pct: Optional[float]
    profit_factor: Optional[float]
    expectancy: Optional[float]
    average_win: Optional[float]
    average_loss: Optional[float]
    largest_win: Optional[float]
    largest_loss: Optional[float]
    longest_losing_streak: int
    max_drawdown_pct: float
    sharpe_ratio: Optional[float]

    def to_dict(self) -> Dict[str, object]:
        """Return metrics as a plain dictionary for text and JSON reports."""
        return asdict(self)


def compute_metrics(
    results: Sequence[TradeResult],
    starting_capital: float = DEFAULT_CAPITAL,
) -> PerformanceMetrics:
    """Calculate all portfolio metrics."""
    nets = [result.net_pnl for result in results]
    curve = build_equity_curve(results, starting_capital)
    ending_equity = curve[-1][1] if curve else starting_capital
    winning_trades = sum(value > 0 for value in nets)
    losing_trades = sum(value < 0 for value in nets)

    return PerformanceMetrics(
        starting_capital=starting_capital,
        ending_equity=ending_equity,
        total_trades=len(nets),
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_net_pnl=round(sum(nets), 6),
        win_rate_pct=win_rate_pct(nets),
        profit_factor=profit_factor(nets),
        expectancy=expectancy(nets),
        average_win=average_win(nets),
        average_loss=average_loss(nets),
        largest_win=largest_win(nets),
        largest_loss=largest_loss(nets),
        longest_losing_streak=longest_losing_streak(results),
        max_drawdown_pct=max_drawdown_pct(curve),
        sharpe_ratio=sharpe_ratio(curve),
    )
