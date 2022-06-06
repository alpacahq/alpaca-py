from alpaca.common.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.models import (
    MarketOrderRequest,
    TrailingStopOrderRequest,
)
import pytest


def test_has_qty_or_notional_but_not_both():

    with pytest.raises(ValueError) as e:
        MarketOrderRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )

    assert "At least one of qty or notional must be provided" in str(e.value)

    with pytest.raises(ValueError) as e:
        MarketOrderRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            qty=5,
            notional=5,
        )

    assert "Both qty and notional can not be set." in str(e.value)


def test_trailing_stop_order_type():

    with pytest.raises(ValueError) as e:
        TrailingStopOrderRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            qty=1,
        )

    assert (
        "Either trail_percent or trail_price must be set for a trailing stop order."
        in str(e.value)
    )

    with pytest.raises(ValueError) as e:
        TrailingStopOrderRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            qty=1,
            trail_percent=2,
            trail_price=5,
        )

    assert "Both trail_percent and trail_price cannot be set." in str(e.value)
