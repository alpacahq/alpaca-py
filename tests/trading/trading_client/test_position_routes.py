from uuid import UUID

from alpaca.common.enums import BaseURL
from alpaca.common.models import (
    Position,
    ClosePositionResponse,
    Order,
    ClosePositionRequest,
)
from alpaca.trading.client import TradingClient

import pytest


@pytest.fixture
def trading_client():
    client = TradingClient("key-id", "secret-key")
    return client


def test_get_all_positions(reqmock, trading_client: TradingClient):

    reqmock.get(
        f"{BaseURL.TRADING_PAPER}/v2/positions",
        text="""
        [
            {
              "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
              "symbol": "AAPL",
              "exchange": "NASDAQ",
              "asset_class": "us_equity",
              "avg_entry_price": "100.0",
              "qty": "5",
              "side": "long",
              "market_value": "600.0",
              "cost_basis": "500.0",
              "unrealized_pl": "100.0",
              "unrealized_plpc": "0.20",
              "unrealized_intraday_pl": "10.0",
              "unrealized_intraday_plpc": "0.0084",
              "current_price": "120.0",
              "lastday_price": "119.0",
              "change_today": "0.0084"
            }
        ]
        """,
    )

    positions = trading_client.get_all_positions()

    assert reqmock.called_once
    assert isinstance(positions, list)
    assert isinstance(positions[0], Position)


def test_get_open_position_with_asset_id(reqmock, trading_client: TradingClient):
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.get(
        f"{BaseURL.TRADING_PAPER}/v2/positions/{asset_id}",
        text=f"""
        {{
          "asset_id": "{asset_id}",
          "symbol": "AAPL",
          "exchange": "NASDAQ",
          "asset_class": "us_equity",
          "avg_entry_price": "100.0",
          "qty": "5",
          "side": "long",
          "market_value": "600.0",
          "cost_basis": "500.0",
          "unrealized_pl": "100.0",
          "unrealized_plpc": "0.20",
          "unrealized_intraday_pl": "10.0",
          "unrealized_intraday_plpc": "0.0084",
          "current_price": "120.0",
          "lastday_price": "119.0",
          "change_today": "0.0084"
        }}
        """,
    )

    position = trading_client.get_open_position(asset_id)

    assert reqmock.called_once
    assert isinstance(position, Position)
    assert position.asset_id == asset_id


def test_get_open_position_with_symbol(reqmock, trading_client: TradingClient):
    symbol = "AAPL"

    reqmock.get(
        f"{BaseURL.TRADING_PAPER}/v2/positions/{symbol}",
        text=f"""
        {{
          "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
          "symbol": "{symbol}",
          "exchange": "NASDAQ",
          "asset_class": "us_equity",
          "avg_entry_price": "100.0",
          "qty": "5",
          "side": "long",
          "market_value": "600.0",
          "cost_basis": "500.0",
          "unrealized_pl": "100.0",
          "unrealized_plpc": "0.20",
          "unrealized_intraday_pl": "10.0",
          "unrealized_intraday_plpc": "0.0084",
          "current_price": "120.0",
          "lastday_price": "119.0",
          "change_today": "0.0084"
        }}
        """,
    )

    position = trading_client.get_open_position(symbol)

    assert reqmock.called_once
    assert isinstance(position, Position)
    assert position.symbol == symbol


def test_close_all_positions(reqmock, trading_client: TradingClient):

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/positions",
        text="""
        [
            {
                "order_id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
                "status_code": 201
            }
        ]
        """,
    )

    close_orders = trading_client.close_all_positions(True)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"cancel_orders": ["true"]}
    assert isinstance(close_orders, list)
    assert isinstance(close_orders[0], ClosePositionResponse)


def test_close_position_with_id(reqmock, trading_client: TradingClient):
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/positions/{asset_id}",
        text=f"""
            {{
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
              "asset_id": "{asset_id}",
              "symbol": "AAPL",
              "asset_class": "us_equity",
              "notional": "500",
              "qty": null,
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
            }}
        """,
    )

    close_order = trading_client.close_position(asset_id)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {}
    assert isinstance(close_order, Order)
    assert close_order.asset_id == asset_id


def test_close_position_with_symbol(reqmock, trading_client: TradingClient):
    symbol = "AAPL"

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/positions/{symbol}",
        text=f"""
            {{
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
              "symbol": "{symbol}",
              "asset_class": "us_equity",
              "notional": "500",
              "qty": null,
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
            }}
        """,
    )

    close_order = trading_client.close_position(symbol)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {}
    assert isinstance(close_order, Order)
    assert close_order.symbol == symbol


def test_close_position_with_qty(reqmock, trading_client: TradingClient):
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/positions/{asset_id}",
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
          "notional": "500",
          "qty": null,
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

    close_options = ClosePositionRequest(qty="100")
    close_order = trading_client.close_position(asset_id, close_options)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"qty": ["100"]}
    assert isinstance(close_order, Order)


def test_close_position_with_percentage(reqmock, trading_client: TradingClient):
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.delete(
        f"{BaseURL.TRADING_PAPER}/v2/positions/{asset_id}",
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
          "notional": "500",
          "qty": null,
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

    close_options = ClosePositionRequest(percentage="0.5")
    close_order = trading_client.close_position(asset_id, close_options)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"percentage": ["0.5"]}
    assert isinstance(close_order, Order)
