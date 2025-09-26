import uuid
import warnings

import pytest

from alpaca.trading.enums import (
    OrderClass,
    OrderSide,
    OrderType,
    TimeInForce,
    TradeEvent,
)
from alpaca.trading.models import TradeUpdate
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    OptionLegRequest,
    TrailingStopOrderRequest,
)


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


def test_notional_works():
    mo = MarketOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        notional=5,
    )

    lo = LimitOrderRequest(
        symbol="BTC/USD",
        side=OrderSide.BUY,
        limit_price=5,
        time_in_force=TimeInForce.DAY,
        notional=50,
    )

    assert mo.type == OrderType.MARKET

    assert lo.type == OrderType.LIMIT


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


def test_mleg_options() -> None:
    symbols = [
        "AAPL250117P00200000",
        "AAPL250117P00250000",
        "AAPL250117P00300000",
        "AAPL250117P00350000",
        "AAPL250117P00400000",
    ]

    def kwargs_as_string(**kwargs):
        return ", ".join([f"{k}={v}" for k, v in kwargs.items()])

    def order_request_factory(is_market: bool):
        if is_market:

            def factory(warn_validated: bool = True, **kwargs):
                o = MarketOrderRequest(**kwargs)
                if warn_validated:
                    warnings.warn(
                        f"MarketOrderRequest({kwargs_as_string(**kwargs)}) passed validation!"
                    )
                return o

        else:

            def factory(warn_validated: bool = True, **kwargs):
                o = LimitOrderRequest(limit_price=1, **kwargs)
                if warn_validated:
                    warnings.warn(
                        f"LimitOrderRequest({kwargs_as_string(**kwargs)}) passed validation!"
                    )
                return o

        return factory

    for is_mkt in [True, False]:
        o_req = order_request_factory(is_mkt)

        # Good requests
        for sym_index in range(2, 5):
            o_req(
                warn_validated=False,
                qty=1,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=[
                    OptionLegRequest(symbol=symbol, ratio_qty=1, side=OrderSide.BUY)
                    for symbol in symbols[:sym_index]
                ],
            )

        # Bad requests
        with pytest.raises(ValueError) as e:
            # Missing qty
            o_req(
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=[
                    OptionLegRequest(
                        symbol=symbols[0], ratio_qty=1, side=OrderSide.BUY
                    ),
                    OptionLegRequest(
                        symbol=symbols[1], ratio_qty=1, side=OrderSide.SELL
                    ),
                ],
            )
        assert "At least one of qty or notional must be provided" in str(e.value)

        with pytest.raises(ValueError) as e:
            # Too few legs
            o_req(
                qty=1,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=[
                    OptionLegRequest(symbol=symbols[0], ratio_qty=1, side=OrderSide.BUY)
                ],
            )
        assert "At least 2 legs are required for the mleg order class" in str(e.value)

        with pytest.raises(ValueError) as e:
            # Too many legs
            o_req(
                qty=1,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=[
                    OptionLegRequest(symbol=symbol, ratio_qty=1, side=OrderSide.BUY)
                    for symbol in symbols
                ],
            )
        assert "At most 4 legs are allowed for the mleg order class." in str(e.value)

        with pytest.raises(ValueError) as e:
            # Missing legs
            o_req(qty=1, time_in_force=TimeInForce.DAY, order_class=OrderClass.MLEG)
        assert "legs is required for the mleg order class." in str(e.value)

        with pytest.raises(ValueError) as e:
            # Repeated symbols across legs
            o_req(
                qty=1,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=[
                    OptionLegRequest(
                        symbol=symbols[0], ratio_qty=1, side=OrderSide.BUY
                    ),
                    OptionLegRequest(
                        symbol=symbols[0], ratio_qty=1, side=OrderSide.SELL
                    ),
                ],
            )

        assert "All legs must have unique symbols." in str(e.value)

        with pytest.raises(ValueError) as e:
            # Legs in non-MLEG order
            o_req(
                qty=1,
                time_in_force=TimeInForce.DAY,
                legs=[
                    OptionLegRequest(symbol=symbols[0], ratio_qty=1, side=OrderSide.BUY)
                ],
            )


def test_trade_update_events() -> None:
    base = {
        "timestamp": "2025-01-01T11:11:11.123456Z",
        "event": "accepted",
        "order": {
            "id": uuid.uuid4(),
            "client_order_id": "123",
            "created_at": "2025-01-01T11:11:11.123456Z",
            "updated_at": "2025-01-01T11:11:11.123456Z",
            "submitted_at": "2025-01-01T11:11:11.123456Z",
            "order_class": "simple",
            "time_in_force": "day",
            "status": "accepted",
            "extended_hours": False,
        },
    }

    for event in TradeEvent:
        msg = base.copy()
        msg["event"] = event
        TradeUpdate(**msg)
