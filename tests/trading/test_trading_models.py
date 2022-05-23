from alpaca.common.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.models import OrderCreationRequest

import pytest


def test_has_qty_or_notional_but_not_both():

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

    assert "At least one of qty or notional must be provided" in str(e.value)

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            qty=5,
            notional=5,
        )

    assert "Both qty and notional can not be set." in str(e.value)


def test_fractional_orders_have_market_type():

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            qty=1.232,
        )

    assert "Fractional orders are only available for market orders." in str(e.value)

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            notional=1.232,
        )

    assert "Fractional orders are only available for market orders." in str(e.value)


def test_limit_and_stop_limit_order_types():

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            qty=1,
        )

    assert "Limit and stop limit orders must have a limit_price." in str(e.value)

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            qty=1,
            limit_price=12.32,
        )

    assert "limit_price can only be set for limit or stop limit orders." in str(e.value)


def test_stop_and_stop_limit_order_types():

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.DAY,
            qty=1,
        )

    assert "Stop and stop limit orders must have a stop_price." in str(e.value)

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            qty=1,
            stop_price=12.32,
        )

    assert "stop_price can only be set for stop or stop limit orders." in str(e.value)


def test_trailing_stop_order_type():

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.TRAILING_STOP,
            time_in_force=TimeInForce.DAY,
            qty=1,
        )

    assert (
        "Either trail_percent or trail_price must be set for a trailing stop order."
        in str(e.value)
    )

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.TRAILING_STOP,
            time_in_force=TimeInForce.DAY,
            qty=1,
            trail_percent=2,
            trail_price=5,
        )

    assert "Both trail_percent and trail_price cannot be set." in str(e.value)

    with pytest.raises(ValueError) as e:
        OrderCreationRequest(
            symbol="SPY",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            qty=1,
            trail_percent=2,
        )

    assert (
        "trail_percent and trail_price may be set only for trailing stop orders."
        in str(e.value)
    )
