from perfkit.sizing import position_size


def test_position_size_example_and_lot_rounding():
    assert position_size(1_000_000, 1, 500, 490) == 1000
    assert position_size(1000, 1, 10, 9, lot_size=10) == 10


def test_position_size_uses_exact_decimal_prices():
    assert position_size(250000, 1.5, 431.35, 431.25) == 37500


def test_zero_capital_is_rejected():
    try:
        position_size(0, 1, 10, 9)
    except ValueError:
        pass
    else:
        raise AssertionError("Zero capital should be rejected")


def test_risk_outside_allowed_range_is_rejected():
    for risk in (0, 101):
        try:
            position_size(100, risk, 10, 9)
        except ValueError:
            continue
        raise AssertionError("Invalid risk should be rejected")


def test_entry_equal_to_stop_is_rejected():
    try:
        position_size(100, 1, 10, 10)
    except ValueError:
        pass
    else:
        raise AssertionError("Equal entry and stop should be rejected")


def test_invalid_lot_size_is_rejected():
    try:
        position_size(100, 1, 10, 9, lot_size=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Zero lot size should be rejected")
