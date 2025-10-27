import warnings
from uuid import UUID
import pytest

from alpaca.common.enums import BaseURL
from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    OrderClass,
    OrderSide,
    OrderStatus,
    PositionIntent,
    TimeInForce,
)
from alpaca.trading.models import Order
from alpaca.trading.requests import (
    CancelOrderResponse,
    GetOrderByIdRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    OptionLegRequest,
    ReplaceOrderRequest,
    StopLossRequest,
    TakeProfitRequest,
)


def test_market_order(reqmock, trading_client):
    reqmock.post(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders",
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
          "symbol": "AAPL`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 1,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "market",
          "type": "market",
          "side": "buy",
          "time_in_force": "day",
          "limit_price": null,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "position_intent": "buy_to_open",
          "commission": 1.25
        }
        """,
    )

    # Market Order
    mo = MarketOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        qty=1,
    )

    mo_response = trading_client.submit_order(mo)

    assert mo_response.status == OrderStatus.ACCEPTED


def test_get_orders(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders",
        text="""
        [
            {
                "id": "0b11f089-722d-4ced-9beb-e2eeed3637dc",
                "client_order_id": "string",
                "created_at": "2019-08-24T14:15:22Z",
                "updated_at": "2019-08-24T14:15:22Z",
                "submitted_at": "2019-08-24T14:15:22Z",
                "filled_at": "2019-08-24T14:15:22Z",
                "expired_at": "2019-08-24T14:15:22Z",
                "canceled_at": "2019-08-24T14:15:22Z",
                "failed_at": "2019-08-24T14:15:22Z",
                "replaced_at": "2019-08-24T14:15:22Z",
                "replaced_by": "0b11f089-722d-4ced-9beb-e2eeed3637dc",
                "replaces": "9f7d75bc-a9a2-40b0-9082-0fc0a09817ff",
                "asset_id": "b4695157-0d1d-4da0-8f9e-5c53149389e4",
                "symbol": "SPY",
                "asset_class": "us_equity",
                "notional": null,
                "qty": 1,
                "filled_qty": 0,
                "filled_avg_price": 0,
                "order_class": "simple",
                "order_type": "market",
                "type": "stop",
                "side": "buy",
                "time_in_force": "day",
                "limit_price": null,
                "stop_price": null,
                "status": "new",
                "extended_hours": true,
                "trail_percent": null,
                "trail_price": null,
                "hwm": "string"
            }
        ]
        """,
    )

    get_orders_request = GetOrdersRequest(symbols=["SPY", "AAPL"])

    response = trading_client.get_orders(get_orders_request)

    assert type(response) is list
    assert type(response[0]) is Order


def test_get_order_by_id(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"

    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders/{order_id}",
        text="""
    {
        "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
        "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
        "created_at": "2021-03-16T18:38:01.942282Z",
        "updated_at": "2021-03-16T18:38:01.942282Z",
        "submitted_at": "2021-03-16T18:38:01.937734Z",
        "filled_at": null,
        "expired_at": null,
        "canceled_at": null,
        "failed_at": null,
        "replaced_at": null,
        "replaced_by": null,
        "replaces": null,
        "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
        "symbol": "AAPL`",
        "asset_class": "us_equity",
        "notional": null,
        "qty": 1,
        "filled_qty": "0",
        "filled_avg_price": null,
        "order_class": "simple",
        "order_type": "market",
        "type": "market",
        "side": "buy",
        "time_in_force": "day",
        "limit_price": null,
        "stop_price": null,
        "status": "accepted",
        "extended_hours": false,
        "legs": null,
        "trail_percent": null,
        "trail_price": null,
        "hwm": null,
        "position_intent": "buy_to_open",
        "commission": 1.25
    }
    """,
    )

    order_request = GetOrderByIdRequest(nested=False)

    order = trading_client.get_order_by_id(order_id=order_id, filter=order_request)

    assert type(order) is Order


def test_get_order_by_client_id(reqmock, trading_client: TradingClient):
    client_id = "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4"

    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders:by_client_order_id?client_order_id={client_id}",
        text="""
    {
        "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
        "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
        "created_at": "2021-03-16T18:38:01.942282Z",
        "updated_at": "2021-03-16T18:38:01.942282Z",
        "submitted_at": "2021-03-16T18:38:01.937734Z",
        "filled_at": null,
        "expired_at": null,
        "canceled_at": null,
        "failed_at": null,
        "replaced_at": null,
        "replaced_by": null,
        "replaces": null,
        "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
        "symbol": "AAPL`",
        "asset_class": "us_equity",
        "notional": null,
        "qty": 1,
        "filled_qty": "0",
        "filled_avg_price": null,
        "order_class": "simple",
        "order_type": "market",
        "type": "market",
        "side": "buy",
        "time_in_force": "day",
        "limit_price": null,
        "stop_price": null,
        "status": "accepted",
        "extended_hours": false,
        "legs": null,
        "trail_percent": null,
        "trail_price": null,
        "hwm": null,
        "position_intent": "buy_to_open",
        "commission": 1.25
    }
    """,
    )

    order = trading_client.get_order_by_client_id(client_id=client_id)

    assert type(order) is Order


def test_replace_order(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"

    reqmock.patch(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders/{order_id}",
        text="""
    {
        "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
        "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
        "created_at": "2021-03-16T18:38:01.942282Z",
        "updated_at": "2021-03-16T18:38:01.942282Z",
        "submitted_at": "2021-03-16T18:38:01.937734Z",
        "filled_at": null,
        "expired_at": null,
        "canceled_at": null,
        "failed_at": null,
        "replaced_at": null,
        "replaced_by": null,
        "replaces": null,
        "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
        "symbol": "AAPL`",
        "asset_class": "us_equity",
        "notional": null,
        "qty": 1,
        "filled_qty": "0",
        "filled_avg_price": null,
        "order_class": "simple",
        "order_type": "market",
        "type": "market",
        "side": "buy",
        "time_in_force": "day",
        "limit_price": null,
        "stop_price": null,
        "status": "accepted",
        "extended_hours": false,
        "legs": null,
        "trail_percent": null,
        "trail_price": null,
        "hwm": null,
        "position_intent": "buy_to_open",
        "commission": 1.25
    }
    """,
    )

    replace_order_request = ReplaceOrderRequest(qty=1)

    order = trading_client.replace_order_by_id(order_id, replace_order_request)

    assert type(order) is Order


def test_replace_order_validate_replace_request() -> None:
    # qty
    ReplaceOrderRequest(qty=1)
    with pytest.raises(ValueError):
        ReplaceOrderRequest(qty=0)
        ReplaceOrderRequest(qty=0, limit_price=0.1)
        ReplaceOrderRequest(qty=0, stop_price=0.1)
        ReplaceOrderRequest(qty=0, trail=0.1)

    # limit_price
    ReplaceOrderRequest(limit_price=0.1)
    ReplaceOrderRequest(qty=1, limit_price=0.1)
    ReplaceOrderRequest(limit_price=0)
    ReplaceOrderRequest(limit_price=-1)

    # stop_price
    ReplaceOrderRequest(stop_price=0.1)
    ReplaceOrderRequest(qty=1, stop_price=0.1)
    with pytest.raises(ValueError):
        ReplaceOrderRequest(stop_price=0)

    # trail
    ReplaceOrderRequest(trail=0.1)
    ReplaceOrderRequest(qty=1, trail=0.1)
    with pytest.raises(ValueError):
        ReplaceOrderRequest(trail=0)


def test_cancel_order_by_id(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    status_code = 204

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders/{order_id}",
        status_code=status_code,
    )

    trading_client.cancel_order_by_id(order_id)

    assert reqmock.called_once


def test_cancel_order_throws_uncancelable_error(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    status_code = 422

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders/{order_id}",
        status_code=status_code,
    )

    with pytest.raises(APIError):
        trading_client.cancel_order_by_id(order_id)

    assert reqmock.called_once


def test_cancel_order_throws_not_found_error(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    status_code = 404

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders/{order_id}",
        status_code=status_code,
    )

    with pytest.raises(APIError):
        trading_client.cancel_order_by_id(order_id)

    assert reqmock.called_once


def test_cancel_orders(reqmock, trading_client: TradingClient):
    status_code = 207

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders",
        status_code=status_code,
        text="""
        [
          {
            "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
            "status": 200
          },
          {
            "id": "72249bb6-6c89-4ea7-b8cf-73f1a140812b",
            "status": 404,
            "body": {"code": 40410000, "message": "order not found"}
           }
        ]
        """,
    )

    response = trading_client.cancel_orders()

    assert type(response) is list
    assert type(response[0]) is CancelOrderResponse
    assert response[0].status == 200
    assert response[0].id == UUID("497f6eca-6276-4993-bfeb-53cbbbba6f08")
    assert response[1].status == 404
    assert response[1].id == UUID("72249bb6-6c89-4ea7-b8cf-73f1a140812b")
    assert response[1].body is not None
    assert response[1].body["code"] == 40410000
    assert response[1].body["message"] == "order not found"


def test_limit_order(reqmock, trading_client):
    reqmock.post(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders",
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
          "symbol": "AAPL`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 1,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "limit",
          "type": "limit",
          "side": "buy",
          "time_in_force": "day",
          "limit_price": 300,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "position_intent": "buy_to_open",
          "commission": 1.25
        }
        """,
    )

    lo = LimitOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        limit_price=300,
        qty=1,
    )

    lo_response = trading_client.submit_order(lo)

    assert lo_response.status == OrderStatus.ACCEPTED


def test_limit_order_request_validation() -> None:
    # missing limit_price for non-OCOC
    with pytest.raises(ValueError):
        # order_class is not specified (default: simple)
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
    with pytest.raises(ValueError):
        # simple
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.SIMPLE,
        )
    with pytest.raises(ValueError):
        # oto with take_profit
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.OTO,
            take_profit=TakeProfitRequest(limit_price=100),
        )
    with pytest.raises(ValueError):
        # oto with stop_loss
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.OTO,
            stop_loss=StopLossRequest(stop_price=300),
        )
    with pytest.raises(ValueError):
        # bracket
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=100),
            stop_loss=StopLossRequest(stop_price=300),
        )
    # no limit_price for OCO
    LimitOrderRequest(
        symbol="AAPL",
        qty=1,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.OCO,
        take_profit=TakeProfitRequest(limit_price=300),
        stop_loss=StopLossRequest(stop_price=100),
    )


def test_order_position_intent(reqmock, trading_client: TradingClient):
    reqmock.post(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders",
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "b4695157-0d1d-4da0-8f9e-5c53149389e4",
          "symbol": "SPY`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 1,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "market",
          "type": "market",
          "side": "buy",
          "time_in_force": "day",
          "limit_price": null,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "position_intent": "buy_to_open",
          "commission": 1.25
        }
        """,
    )

    # Market Order
    mo = MarketOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        qty=1,
        position_intent=PositionIntent.BUY_TO_OPEN,
    )

    assert mo.position_intent == PositionIntent.BUY_TO_OPEN

    mo_response = trading_client.submit_order(mo)

    assert mo_response.status == OrderStatus.ACCEPTED

    reqmock.post(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders",
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
          "symbol": "AAPL`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 1,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "limit",
          "type": "limit",
          "side": "sell",
          "time_in_force": "day",
          "limit_price": 300,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "position_intent": "sell_to_open",
          "commission": 1.25
        }
        """,
    )

    lo = LimitOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        limit_price=300,
        qty=1,
        position_intent=PositionIntent.SELL_TO_OPEN,
    )

    assert lo.position_intent == PositionIntent.SELL_TO_OPEN

    lo_response = trading_client.submit_order(lo)

    assert lo_response.status == OrderStatus.ACCEPTED


def test_mleg_request_validation() -> None:
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
        with pytest.raises(ValueError):
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

        with pytest.raises(ValueError):
            # Too few legs
            o_req(
                qty=1,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=[
                    OptionLegRequest(symbol=symbols[0], ratio_qty=1, side=OrderSide.BUY)
                ],
            )

        with pytest.raises(ValueError):
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

        with pytest.raises(ValueError):
            # Missing legs
            o_req(qty=1, time_in_force=TimeInForce.DAY, order_class=OrderClass.MLEG)

        with pytest.raises(ValueError):
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

        with pytest.raises(ValueError):
            # Legs in non-MLEG order
            o_req(
                qty=1,
                time_in_force=TimeInForce.DAY,
                legs=[
                    OptionLegRequest(symbol=symbols[0], ratio_qty=1, side=OrderSide.BUY)
                ],
            )
