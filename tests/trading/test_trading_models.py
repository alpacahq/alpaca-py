import uuid
import warnings
from typing import Optional

import pytest

from alpaca.trading.enums import (
    OptionDeliverableSettlementMethod,
    OptionDeliverableSettlementType,
    OptionDeliverableType,
    OrderClass,
    OrderSide,
    OrderType,
    TimeInForce,
    TradeEvent,
)
from alpaca.trading.models import OptionDeliverable, TradeUpdate
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    OptionLegRequest,
    StopLossRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
    TakeProfitRequest,
    TrailingStopOrderRequest,
)


@pytest.mark.parametrize("field_name", ["strike_price_gte", "strike_price_lte"])
def test_get_option_contracts_strike_price_filter_type_matches_spec(field_name):
    assert (
        GetOptionContractsRequest.model_fields[field_name].annotation == Optional[float]
    )
    assert f"{field_name} (Optional[float])" in GetOptionContractsRequest.__doc__


def test_option_deliverable_matches_spec():
    deliverable = OptionDeliverable(
        type="equity",
        symbol="AAPL",
        amount="100",
        allocation_percentage="100",
        settlement_type="T+1",
        settlement_method="BTOB",
        delayed_settlement=False,
        asset_id=uuid.UUID(int=0),
    )

    assert deliverable.type == OptionDeliverableType.EQUITY
    assert deliverable.settlement_type == OptionDeliverableSettlementType.T_PLUS_1
    assert deliverable.settlement_method == OptionDeliverableSettlementMethod.BTOB


def test_get_option_contracts_request_added_fields():
    request = GetOptionContractsRequest(
        strike_price_gte=100.5,
        strike_price_lte=200.5,
        ppind=True,
        page_token="next",
    )

    assert request.show_deliverables is True
    assert request.ppind is True
    assert request.page_token == "next"


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


def test_order_requests_reject_incompatible_price_fields():
    base_kwargs = {
        "symbol": "SPY",
        "side": OrderSide.BUY,
        "time_in_force": TimeInForce.DAY,
        "qty": 1,
    }

    with pytest.raises(ValueError, match="limit_price is not supported"):
        MarketOrderRequest(**base_kwargs, limit_price=100)

    with pytest.raises(ValueError, match="stop_price is not supported"):
        MarketOrderRequest(**base_kwargs, stop_price=95)

    with pytest.raises(ValueError, match="stop_price is not supported"):
        LimitOrderRequest(**base_kwargs, limit_price=100, stop_price=95)

    with pytest.raises(ValueError, match="limit_price is not supported"):
        StopOrderRequest(**base_kwargs, limit_price=100, stop_price=95)

    with pytest.raises(ValueError, match="limit_price is not supported"):
        TrailingStopOrderRequest(**base_kwargs, limit_price=100, trail_price=1)

    with pytest.raises(ValueError, match="stop_price is not supported"):
        TrailingStopOrderRequest(**base_kwargs, stop_price=95, trail_price=1)

    with pytest.raises(ValueError, match="trail_price is not supported"):
        MarketOrderRequest(**base_kwargs, trail_price=1)

    with pytest.raises(ValueError, match="trail_percent is not supported"):
        MarketOrderRequest(**base_kwargs, trail_percent=1)

    with pytest.raises(ValueError, match="trail_price is not supported"):
        StopOrderRequest(**base_kwargs, stop_price=95, trail_price=1)

    with pytest.raises(ValueError, match="trail_percent is not supported"):
        LimitOrderRequest(**base_kwargs, limit_price=100, trail_percent=1)

    with pytest.raises(ValueError, match="trail_price is not supported"):
        StopLimitOrderRequest(
            **base_kwargs, limit_price=100, stop_price=95, trail_price=1
        )

    StopLimitOrderRequest(**base_kwargs, limit_price=100, stop_price=95)


def test_advanced_order_classes_require_exit_legs():
    base_kwargs = {
        "symbol": "SPY",
        "side": OrderSide.BUY,
        "time_in_force": TimeInForce.DAY,
        "qty": 1,
    }

    with pytest.raises(ValueError, match="bracket orders require take_profit"):
        MarketOrderRequest(**base_kwargs, order_class=OrderClass.BRACKET)

    with pytest.raises(ValueError, match="bracket orders require stop_loss"):
        MarketOrderRequest(
            **base_kwargs,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=110),
        )

    with pytest.raises(ValueError, match="oco orders require take_profit"):
        LimitOrderRequest(
            **base_kwargs,
            order_class=OrderClass.OCO,
            stop_loss=StopLossRequest(stop_price=90),
        )

    with pytest.raises(ValueError, match="oco orders require stop_loss"):
        LimitOrderRequest(
            **base_kwargs,
            order_class=OrderClass.OCO,
            take_profit=TakeProfitRequest(limit_price=110),
        )

    with pytest.raises(
        ValueError, match="oto orders require either take_profit or stop_loss"
    ):
        MarketOrderRequest(**base_kwargs, order_class=OrderClass.OTO)

    MarketOrderRequest(
        **base_kwargs,
        order_class=OrderClass.OTO,
        take_profit=TakeProfitRequest(limit_price=110),
    )


def test_advanced_order_class_error_message_uses_plain_string_label():
    # Regression test: the error message must read "bracket orders require ..."
    # rather than "OrderClass.BRACKET orders require ...", whether the caller
    # passes the OrderClass enum member or the equivalent raw string.
    base_kwargs = {
        "symbol": "SPY",
        "side": OrderSide.BUY,
        "time_in_force": TimeInForce.DAY,
        "qty": 1,
    }

    with pytest.raises(ValueError, match="bracket orders require take_profit") as e:
        MarketOrderRequest(**base_kwargs, order_class=OrderClass.BRACKET)
    assert "OrderClass.BRACKET" not in str(e.value)

    with pytest.raises(ValueError, match="bracket orders require take_profit") as e:
        MarketOrderRequest(**base_kwargs, order_class="bracket")
    assert "OrderClass.BRACKET" not in str(e.value)


def test_mleg_order_class_only_supports_market_and_limit_requests():
    legs = [
        OptionLegRequest(symbol="AAPL250117P00200000", ratio_qty=1, side=OrderSide.BUY),
        OptionLegRequest(
            symbol="AAPL250117P00250000", ratio_qty=1, side=OrderSide.SELL
        ),
    ]
    base_kwargs = {
        "qty": 1,
        "time_in_force": TimeInForce.DAY,
        "order_class": OrderClass.MLEG,
        "legs": legs,
    }

    MarketOrderRequest(**base_kwargs)
    LimitOrderRequest(**base_kwargs, limit_price=1)

    with pytest.raises(
        ValueError, match="mleg order class only supports market and limit orders"
    ):
        StopOrderRequest(**base_kwargs, stop_price=1)

    with pytest.raises(
        ValueError, match="mleg order class only supports market and limit orders"
    ):
        StopLimitOrderRequest(**base_kwargs, stop_price=1, limit_price=1)

    with pytest.raises(
        ValueError, match="mleg order class only supports market and limit orders"
    ):
        TrailingStopOrderRequest(**base_kwargs, trail_price=1)


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
