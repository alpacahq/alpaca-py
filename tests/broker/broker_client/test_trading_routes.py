import datetime

from alpaca.broker import OrderRequest
from alpaca.broker.client import BrokerClient

from alpaca.common.enums import BaseURL, OrderSide, OrderType, TimeInForce
from alpaca.common.models import (
    Position,
    ClosePositionResponse,
    ClosePositionRequest,
    PortfolioHistory,
    GetPortfolioHistoryRequest,
)
from alpaca.broker.models import Order
from uuid import UUID


def test_get_all_positions_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions",
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

    positions = client.get_all_positions_for_account(account_id)

    assert reqmock.called_once
    assert isinstance(positions, list)
    assert isinstance(positions[0], Position)


def test_get_open_position_for_account_with_asset_id(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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

    position = client.get_open_position_for_account(account_id, asset_id)

    assert reqmock.called_once
    assert isinstance(position, Position)
    assert position.asset_id == asset_id


def test_get_open_position_for_account_with_symbol(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    symbol = "AAPL"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions/{symbol}",
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

    position = client.get_open_position_for_account(account_id, symbol)

    assert reqmock.called_once
    assert isinstance(position, Position)
    assert position.symbol == symbol


def test_close_all_positions_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions",
        text="""
        [
            {
                "order_id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
                "status_code": 201
            }
        ]
        """,
    )

    close_orders = client.close_all_positions_for_account(account_id, True)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"cancel_orders": ["true"]}
    assert isinstance(close_orders, list)
    assert isinstance(close_orders[0], ClosePositionResponse)


def test_close_position_for_account_with_id(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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

    close_order = client.close_position_for_account(account_id, asset_id)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {}
    assert isinstance(close_order, Order)
    assert close_order.asset_id == asset_id


def test_close_position_for_account_with_symbol(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    symbol = "AAPL"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions/{symbol}",
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

    close_order = client.close_position_for_account(account_id, symbol)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {}
    assert isinstance(close_order, Order)
    assert close_order.symbol == symbol


def test_close_position_for_account_with_qty(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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
    close_order = client.close_position_for_account(account_id, asset_id, close_options)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"qty": ["100"]}
    assert isinstance(close_order, Order)


def test_close_position_for_account_with_percentage(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    asset_id = UUID("904837e3-3b76-47ec-b432-046db621571b")

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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
    close_order = client.close_position_for_account(account_id, asset_id, close_options)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"percentage": ["0.5"]}
    assert isinstance(close_order, Order)


def test_get_portfolio_history(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/account/portfolio/history",
        text="""
        {
          "timestamp": [1580826600000, 1580827500000, 1580828400000],
          "equity": [27423.73, 27408.19, 27515.97],
          "profit_loss": [11.8, -3.74, 104.04],
          "profit_loss_pct": [
            0.000430469507254688, -0.0001364369455197062, 0.0037954277571845543
          ],
          "base_value": 27411.93,
          "timeframe": "15Min"
        }
        """,
    )

    portfolio_history = client.get_portfolio_history_for_account(account_id)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {}
    assert isinstance(portfolio_history, PortfolioHistory)


def test_get_portfolio_history_with_filter(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/account/portfolio/history",
        text="""
        {
          "timestamp": [1580826600000, 1580827500000, 1580828400000],
          "equity": [27423.73, 27408.19, 27515.97],
          "profit_loss": [11.8, -3.74, 104.04],
          "profit_loss_pct": [
            0.000430469507254688, -0.0001364369455197062, 0.0037954277571845543
          ],
          "base_value": 27411.93,
          "timeframe": "15Min"
        }
        """,
    )

    history_filter = GetPortfolioHistoryRequest(
        period="1M",
        timeframe="15M",
        date_end=datetime.date(2022, 1, 1),
        extended_hours=True,
    )
    portfolio_history = client.get_portfolio_history_for_account(
        account_id, history_filter
    )

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {
        "period": ["1m"],
        "timeframe": ["15m"],
        "date_end": ["2022-01-01"],
        "extended_hours": ["true"],
    }
    assert isinstance(portfolio_history, PortfolioHistory)


def test_submit_order_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    symbol = "AAPL"
    amount_notional = '10'
    commission = 1.0

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/orders",
        text=f"""
        {{
            "id": "e8da0077-82c2-438c-8829-994cbdabd0b7",
            "client_order_id": "16a27e2b-7d68-4f4b-8671-a96534a9282b",
            "created_at": "2022-11-07T18:49:31.993298206Z",
            "updated_at": "2022-11-07T18:49:31.993343456Z",
            "submitted_at": "2022-11-07T18:49:31.992088526Z",
            "filled_at": null,
            "expired_at": null,
            "canceled_at": null,
            "failed_at": null,
            "replaced_at": null,
            "replaced_by": null,
            "replaces": null,
            "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
            "symbol": "{symbol}",
            "asset_class": "us_equity",
            "notional": "{amount_notional}",
            "qty": null,
            "filled_qty": "0",
            "filled_avg_price": null,
            "order_class": "",
            "order_type": "market",
            "type": "market",
            "side": "buy",
            "time_in_force": "day",
            "limit_price": null,
            "stop_price": null,
            "status": "pending_new",
            "extended_hours": false,
            "legs": null,
            "trail_percent": null,
            "trail_price": null,
            "hwm": null,
            "commission": "{commission}",
            "subtag": null,
            "source": null
        }}
        """,
    )

    order_req = OrderRequest(
        symbol=symbol,
        qty=0,
        notional=amount_notional,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        commission=commission
    )

    order = client.submit_order_for_account(account_id, order_req)
    assert reqmock.called_once
    assert isinstance(order, Order)
    assert order.notional == amount_notional
    assert order.commission == commission
