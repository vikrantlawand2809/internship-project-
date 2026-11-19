import math
from decimal import Decimal


def position_size(
    capital: float,
    risk_pct: float,
    entry: float,
    stop: float,
    lot_size: int = 1,
) -> int:
    """Calculate shares from risk budget, rounded down to a lot multiple."""
    for name, value in (
        ("capital", capital), ("risk_pct", risk_pct),
        ("entry", entry), ("stop", stop),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(name + " must be a number")
        if not math.isfinite(value):
            raise ValueError(name + " must be finite")

    if capital <= 0:
        raise ValueError("capital must be greater than zero")
    if not 0 < risk_pct <= 100:
        raise ValueError("risk_pct must be in (0, 100]")
    if isinstance(lot_size, bool) or not isinstance(lot_size, int) or lot_size < 1:
        raise ValueError("lot_size must be a whole number above zero")
    if entry == stop:
        raise ValueError("entry and stop must be different")

    # Decimal keeps prices such as 431.35 - 431.25 exact before rounding down.
    risk_money = Decimal(str(capital)) * Decimal(str(risk_pct)) / 100
    loss_per_share = abs(Decimal(str(entry)) - Decimal(str(stop)))
    shares = int(risk_money / loss_per_share)
    return shares // lot_size * lot_size
