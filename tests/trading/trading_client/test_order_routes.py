from alpaca.common.exceptions import APIError
from alpaca.trading.requests import (
    GetOrderByIdRequest,
    GetOrdersRequest,
    ReplaceOrderRequest,
    CancelOrderResponse,
    MarketOrderRequest,
    LimitOrderRequest,
)
from alpaca.trading.models import Order
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderStatus, TimeInForce
from alpaca.common.enums import BaseURL

import pytest


def test_market_order(reqmock, trading_client):

    reqmock.post(
        f"{BaseURL.TRADING_PAPER}/v2/orders",
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
        f"{BaseURL.TRADING_PAPER}/v2/orders",
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
        f"{BaseURL.TRADING_PAPER}/v2/orders/{order_id}",
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
        f"{BaseURL.TRADING_PAPER}/v2/orders:by_client_order_id?client_order_id={client_id}",
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
        "commission": 1.25
    }
    """,
    )

    order = trading_client.get_order_by_client_id(client_id=client_id)

    assert type(order) is Order


def test_replace_order(reqmock, trading_client: TradingClient):

    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"

    reqmock.patch(
        f"{BaseURL.TRADING_PAPER}/v2/orders/{order_id}",
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
        "commission": 1.25
    }
    """,
    )

    replace_order_request = ReplaceOrderRequest(qty=1)

    order = trading_client.replace_order_by_id(order_id, replace_order_request)

    assert type(order) is Order


def test_cancel_order_by_id(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    status_code = 204

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/orders/{order_id}",
        status_code=status_code,
    )

    trading_client.cancel_order_by_id(order_id)

    assert reqmock.called_once


def test_cancel_order_throws_uncancelable_error(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    status_code = 422

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/orders/{order_id}",
        status_code=status_code,
    )

    with pytest.raises(APIError):
        trading_client.cancel_order_by_id(order_id)

    assert reqmock.called_once


def test_cancel_order_throws_not_found_error(reqmock, trading_client: TradingClient):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    status_code = 404

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/orders/{order_id}",
        status_code=status_code,
    )

    with pytest.raises(APIError):
        trading_client.cancel_order_by_id(order_id)

    assert reqmock.called_once


def test_cancel_orders(reqmock, trading_client: TradingClient):

    status_code = 207

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/orders",
        status_code=status_code,
        text="""
        [
          {
            "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
            "status": 200
          }
        ]
        """,
    )

    response = trading_client.cancel_orders()

    assert type(response) is list
    assert type(response[0]) is CancelOrderResponse
    assert response[0].status == 200


def test_limit_order(reqmock, trading_client):
    reqmock.post(
        f"{BaseURL.TRADING_PAPER}/v2/orders",
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
