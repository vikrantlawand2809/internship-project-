from typing import Dict, List
import backtesting
import pandas as pd
from backtesting import Backtest, Strategy
from part_a.fix import patched_pl_pct, position_pl_pct
def _prices() -> pd.DataFrame:
    prices = [10, 10, 10, 100, 15, 15]
    data = pd.DataFrame({
        "Open": prices,
        "High": prices,
        "Low": prices,
        "Close": prices,
    })
    data.index = pd.date_range("2024-01-01", periods=len(prices))
    return data


def run_scenario(
    side: str = "LONG",
    patched: bool = False,
    two_trades: bool = True,
    open_trade: bool = True,
) -> Dict[str, float]:
    """Run actual backtesting.py code and return values at the test bar."""
    if side not in ("LONG", "SHORT"):
        raise ValueError("side must be LONG or SHORT")
    if backtesting.__version__ != "0.6.2":
        raise RuntimeError("Install backtesting==0.6.2 to run this example")

    class ExampleStrategy(Strategy):
        def init(self) -> None:
            self.result = {}

        def next(self) -> None:
            bar = len(self.data) - 1
            order = self.buy if side == "LONG" else self.sell

            # Orders are placed on separate bars so they enter at prices 10 and 100.
            if bar == 1 and open_trade:
                order(size=10)
            elif bar == 2 and two_trades and open_trade:
                order(size=1)
            elif bar == 4:
                self.result = {
                    "pl": self.position.pl,
                    "pl_pct": self.position.pl_pct,
                    "fixed_pct": position_pl_pct(self.trades),
                }

    def run() -> Dict[str, float]:
        backtest = Backtest(
            _prices(), ExampleStrategy, cash=100_000, commission=0
        )
        return backtest.run()["_strategy"].result

    if patched:
        with patched_pl_pct():
            return run()
    return run()


def main() -> None:
    for side in ("LONG", "SHORT"):
        result = run_scenario(side)
        fixed = run_scenario(side, patched=True)
        print(side)
        print("  Cash P&L:", round(result["pl"], 2))
        print("  Original percentage:", round(result["pl_pct"] * 100, 2), "%")
        print("  Correct percentage:", round(fixed["pl_pct"] * 100, 2), "%")


if __name__ == "__main__":
    main()
