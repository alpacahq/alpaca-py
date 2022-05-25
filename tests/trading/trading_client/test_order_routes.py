from alpaca.trading.client import TradingClient
from alpaca.common.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from alpaca.trading.models import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    TrailingStopOrderRequest,
)
from alpaca.common.enums import BaseURL

import pytest


@pytest.fixture
def trading_client():
    client = TradingClient("key-id", "secret-key")
    return client


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
