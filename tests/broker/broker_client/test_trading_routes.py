import datetime
from alpaca.broker.client import BrokerClient
from alpaca.common.enums import BaseURL
from alpaca.trading.requests import (
    CancelOrderResponse,
    ClosePositionRequest,
    GetPortfolioHistoryRequest,
)
from alpaca.trading.models import (
    Position,
    ClosePositionResponse,
    PortfolioHistory,
    AllAccountsPositions,
)
from alpaca.broker.models import Order
from uuid import UUID


def test_get_all_accounts_positions(reqmock, client: BrokerClient):
    account_id = "02c64fbb-35f0-4403-9015-e5eac4b7ef70"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/positions",
        text="""
        {
            "as_of": "2023-03-29T16:00:00-04:00",
            "positions": {
                "02c64fbb-35f0-4403-9015-e5eac4b7ef70": [
                    {
                        "asset_id": "8ccae427-5dd0-45b3-b5fe-7ba5e422c766",
                        "symbol": "TSLA",
                        "exchange": "NASDAQ",
                        "asset_class": "us_equity",
                        "asset_marginable": true,
                        "qty": "0.173011547",
                        "avg_entry_price": "286.9749783265074366",
                        "side": "long",
                        "market_value": "32.73205457693",
                        "cost_basis": "49.6499849505605227113711001112",
                        "unrealized_pl": "-16.9179303736305227113711001112",
                        "unrealized_plpc": "-0.340743917454894",
                        "unrealized_intraday_pl": "-16.9179303736305227113711001112",
                        "unrealized_intraday_plpc": "-0.340743917454894",
                        "current_price": "189.19",
                        "lastday_price": "189.19",
                        "change_today": "0",
                        "swap_rate": "1.499868775739003",
                        "avg_entry_swap_rate": "1.4947236256016263",
                        "usd": {
                            "avg_entry_price": "191.992",
                            "market_value": "21.8232788803824064",
                            "cost_basis": "33.216832931624",
                            "unrealized_pl": "-11.2796070211508065",
                            "unrealized_plpc": "-0.340743917454894",
                            "unrealized_intraday_pl": "-11.2796070211508065",
                            "unrealized_intraday_plpc": "-0.340743917454894",
                            "current_price": "126.13770155111327",
                            "lastday_price": "126.13770155111327",
                            "change_today": "0"
                        },
                        "qty_available": "0.173011547"
                    }
                ]
            }
        }
        """,
    )

    all_accounts_positions = client.get_all_accounts_positions()

    assert reqmock.called_once
    assert isinstance(all_accounts_positions, AllAccountsPositions)
    assert isinstance(all_accounts_positions.positions, dict)
    assert isinstance(all_accounts_positions.positions[account_id], list)
    assert isinstance(all_accounts_positions.positions[account_id][0], Position)


def test_get_all_positions_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions",
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
                "change_today": "0.0084",
                "usd": {
                    "avg_entry_price": "100.0",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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
            "change_today": "0.0084",
            "usd": {{
                "avg_entry_price": "100.0",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions/{symbol}",
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
            "change_today": "0.0084",
            "usd": {{
                "avg_entry_price": "100.0",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions",
        text="""
        [
            {
                "symbol": "BTCUSD",
                "status": 200,
                "body": {
                    "id": "e6419d12-56e4-4d67-a61b-f6e464e1f8a8",
                    "client_order_id": "c6814ede-8c93-4480-9a27-7a00853d9881",
                    "created_at": "2022-07-27T08:12:33.66897767Z",
                    "updated_at": "2022-07-27T08:12:33.66902729Z",
                    "submitted_at": "2022-07-27T08:12:33.667750101Z",
                    "filled_at": null,
                    "expired_at": null,
                    "canceled_at": null,
                    "failed_at": null,
                    "replaced_at": null,
                    "replaced_by": null,
                    "replaces": null,
                    "asset_id": "276e2673-764b-4ab6-a611-caf665ca6340",
                    "symbol": "BTC/USD",
                    "asset_class": "crypto",
                    "notional": null,
                    "qty": "0.0283",
                    "filled_qty": "0",
                    "filled_avg_price": null,
                    "order_class": "",
                    "order_type": "market",
                    "type": "market",
                    "side": "sell",
                    "time_in_force": "gtc",
                    "limit_price": null,
                    "stop_price": null,
                    "status": "pending_new",
                    "extended_hours": false,
                    "legs": null,
                    "trail_percent": null,
                    "trail_price": null,
                    "hwm": null,
                    "position_intent": "buy_to_open",
                    "subtag": null,
                    "source": null
                }
            },
            {
                "symbol": "SQQQ",
                "status": 403,
                "body": {
                    "available": "0",
                    "code": 40310000,
                    "existing_qty": "1000",
                    "held_for_orders": "1000",
                    "message": "insufficient qty available for order (requested: 1000, available: 0)",
                    "symbol": "SQQQ"
                }
            },
            {
                "symbol": "NYC",
                "status": 403,
                "body": {
                    "code": 40310000,
                    "message": "account is not allowed to short"
                }
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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
              "position_intent": "buy_to_open",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions/{symbol}",
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
              "position_intent": "buy_to_open",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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
          "position_intent": "buy_to_open",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/positions/{asset_id}",
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
          "position_intent": "buy_to_open",
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/account/portfolio/history",
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


def test_get_portfolio_history_with_null_pl_pct(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/account/portfolio/history",
        text="""
        {
          "timestamp": [1580826600000, 1580827500000, 1580828400000],
          "equity": [27423.73, 27408.19, 27515.97],
          "profit_loss": [11.8, -3.74, 104.04],
          "profit_loss_pct": [null, null, null],
          "base_value": 27411.93,
          "timeframe": "15Min"
        }
        """,
    )

    portfolio_history = client.get_portfolio_history_for_account(account_id)

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {}
    assert isinstance(portfolio_history, PortfolioHistory)


def test_get_portfolio_history_with_null_base_value(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/account/portfolio/history",
        text="""
        {
          "timestamp": [1580826600000, 1580827500000, 1580828400000],
          "equity": [27423.73, 27408.19, 27515.97],
          "profit_loss": [11.8, -3.74, 104.04],
          "profit_loss_pct": [11.8, -3.74, 104.04],
          "base_value": null,
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
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/account/portfolio/history",
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


def test_cancel_orders_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/orders",
        text="""
        [
            {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
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

    res = client.cancel_orders_for_account(account_id)

    assert reqmock.called_once
    assert isinstance(res, list)
    assert isinstance(res[0], CancelOrderResponse)
    assert res[0].id == UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
    assert res[0].status == 200
    assert isinstance(res[1], CancelOrderResponse)
    assert res[1].id == UUID("72249bb6-6c89-4ea7-b8cf-73f1a140812b")
    assert res[1].status == 404
    assert res[1].body is not None
    assert res[1].body["code"] == 40410000
    assert res[1].body["message"] == "order not found"
