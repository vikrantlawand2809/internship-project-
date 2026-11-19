from types import SimpleNamespace

import pytest
from backtesting.backtesting import Position

from part_a.bug_reproduction import run_scenario
from part_a.fix import patched_pl_pct, position_pl_pct


@pytest.mark.xfail(strict=True, reason="Demonstrates the original library bug")
def test_original_long_percentage_has_wrong_sign():
    # This assertion would be correct if the library did not have the bug.
    assert run_scenario("LONG")["pl_pct"] < 0


@pytest.mark.xfail(strict=True, reason="Demonstrates the original library bug")
def test_original_short_percentage_has_wrong_sign():
    assert run_scenario("SHORT")["pl_pct"] > 0


def test_fix_corrects_long_and_short_positions():
    long_result = run_scenario("LONG", patched=True)
    short_result = run_scenario("SHORT", patched=True)
    assert long_result["pl_pct"] == pytest.approx(-0.175)
    assert short_result["pl_pct"] == pytest.approx(0.175)


def test_fix_works_for_one_trade_and_no_trades():
    assert run_scenario("LONG", patched=True, two_trades=False)["pl_pct"] == 0.5
    assert position_pl_pct([]) == 0
    empty_position = run_scenario(
        "LONG", patched=True, open_trade=False
    )
    assert empty_position["pl"] == 0
    assert empty_position["pl_pct"] == 0


def test_same_price_trades_agree_with_original():
    trades = [
        SimpleNamespace(pl=50, size=10, entry_price=10),
        SimpleNamespace(pl=-10, size=2, entry_price=10),
    ]
    assert position_pl_pct(trades) == pytest.approx(40 / 120)


def test_patch_restores_original_property():
    original = Position.pl_pct
    with patched_pl_pct():
        assert Position.pl_pct is not original
    assert Position.pl_pct is original
