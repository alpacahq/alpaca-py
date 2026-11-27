"""TradingClient returns the public compatibility shapes, which keep the newer OpenAPI fields.

The generated models replace these shapes once the deprecation window ends.
"""

from datetime import date, datetime

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import (
    AccountConfiguration,
    Asset,
    Calendar,
    CorporateAnnouncement,
    OptionContract,
    PortfolioHistory,
    Position,
    TradeAccount,
)
from alpaca.trading.requests import (
    AdvancedInstructions,
    PatchOrderRequest,
    ReplaceOrderRequest,
)


def test_get_account_keeps_openapi_fields(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account",
        text="""
        {
          "id": "e6fe16f3-64a4-4921-8928-cadf02f92f98",
          "account_number": "010203ABCD",
          "status": "ACTIVE",
          "balance_asof": "2021-04-01",
          "intraday_adjustments": "0",
          "pending_reg_taf_fees": "1.25"
        }
        """,
    )

    account = trading_client.get_account()

    assert isinstance(account, TradeAccount)
    assert account.balance_asof == "2021-04-01"
    assert account.intraday_adjustments == "0"
    assert account.pending_reg_taf_fees == "1.25"


def test_get_account_configurations_keeps_disable_overnight_trading(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/configurations",
        text="""
        {
          "disable_overnight_trading": true,
          "fractional_trading": true,
          "max_margin_multiplier": "4",
          "no_shorting": false,
          "suspend_trade": false,
          "trade_confirm_email": "all",
          "ptp_no_exception_entry": false
        }
        """,
    )

    configurations = trading_client.get_account_configurations()

    assert isinstance(configurations, AccountConfiguration)
    assert configurations.disable_overnight_trading is True


def test_get_asset_keeps_openapi_fields(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/AAPL",
        text="""
        {
          "id": "904837e3-3b76-47ec-b432-046db621571b",
          "class": "us_equity",
          "exchange": "NASDAQ",
          "symbol": "AAPL",
          "name": "Apple Inc. Common Stock",
          "status": "active",
          "tradable": true,
          "marginable": true,
          "shortable": true,
          "fractionable": true,
          "cusip": "037833100",
          "borrow_status": "easy_to_borrow",
          "margin_requirement_long": "25",
          "margin_requirement_short": "30"
        }
        """,
    )

    asset = trading_client.get_asset("AAPL")

    assert isinstance(asset, Asset)
    assert asset.cusip == "037833100"
    assert asset.borrow_status == "easy_to_borrow"
    assert asset.margin_requirement_long == "25"
    assert asset.margin_requirement_short == "30"


def test_get_calendar_keeps_session_fields(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/calendar",
        text="""
        [
          {
            "date": "2022-05-16",
            "open": "09:30",
            "close": "16:00",
            "session_open": "0400",
            "session_close": "2000",
            "settlement_date": "2022-05-18"
          }
        ]
        """,
    )

    result = trading_client.get_calendar()

    assert isinstance(result[0], Calendar)
    assert result[0].date == date(2022, 5, 16)
    assert result[0].open == datetime(2022, 5, 16, 9, 30)
    assert result[0].close == datetime(2022, 5, 16, 16, 0)
    assert result[0].session_open == "0400"
    assert result[0].session_close == "2000"
    assert result[0].settlement_date == date(2022, 5, 18)


def test_get_portfolio_history_keeps_base_value_asof(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/portfolio/history",
        text="""
        {
          "timestamp": [1580826600000],
          "equity": [27423.73],
          "profit_loss": [11.8],
          "profit_loss_pct": [0.00043],
          "base_value": 27411.93,
          "base_value_asof": "2023-10-20",
          "timeframe": "15Min"
        }
        """,
    )

    history = trading_client.get_portfolio_history()

    assert isinstance(history, PortfolioHistory)
    assert history.base_value_asof == date(2023, 10, 20)


def test_get_open_position_keeps_prev_swap_rate(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/positions/AAPL",
        text="""
        {
          "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
          "symbol": "AAPL",
          "exchange": "NASDAQ",
          "asset_class": "us_equity",
          "asset_marginable": true,
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
          "prev_swap_rate": "1.1"
        }
        """,
    )

    position = trading_client.get_open_position("AAPL")

    assert isinstance(position, Position)
    assert position.prev_swap_rate == "1.1"


def test_get_option_contract_keeps_openapi_fields(
    reqmock, trading_client: TradingClient
):
    symbol = "AAPL231103C00170000"
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts/{symbol}",
        text="""
        {
          "id": "00000000-0000-0000-0000-000000000000",
          "symbol": "AAPL231103C00170000",
          "name": "AAPL Nov 03 2023 170 Call",
          "status": "active",
          "tradable": true,
          "expiration_date": "2023-11-03",
          "root_symbol": "AAPL",
          "underlying_symbol": "AAPL",
          "underlying_asset_id": "00000000-0000-0000-0000-000000000000",
          "type": "call",
          "style": "american",
          "strike_price": "170",
          "multiplier": "100",
          "ppind": true,
          "size": "100",
          "deliverables": [
            {
              "type": "equity",
              "symbol": "AAPL",
              "amount": "100",
              "allocation_percentage": "100",
              "settlement_type": "T+1",
              "settlement_method": "BTOB",
              "delayed_settlement": false
            }
          ]
        }
        """,
    )

    contract = trading_client.get_option_contract(symbol)

    assert isinstance(contract, OptionContract)
    assert contract.multiplier == "100"
    assert contract.ppind is True
    assert contract.deliverables[0].symbol == "AAPL"
    assert contract.deliverables[0].amount == "100"


def test_generated_corporate_announcement_keeps_effective_date():
    # The client still returns CorporateActionAnnouncement, which has no
    # effective_date; the generated model that replaces it does.
    announcement = CorporateAnnouncement.model_validate(
        {
            "id": "be3c368a-4c7c-4384-808e-f02c9f5a8afe",
            "ca_type": "Dividend",
            "effective_date": "2021-01-14",
        }
    )

    assert announcement.effective_date == date(2021, 1, 14)


def test_replace_order_accepts_patch_and_replace_requests(
    reqmock, trading_client: TradingClient
):
    order_id = "61e69015-8549-4bfd-b9c3-01e75843f47d"
    order_response = """
    {
      "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
      "client_order_id": "c6814ede-8c93-4480-9a27-7a00853d9881",
      "created_at": "2021-03-16T18:38:01.942282Z",
      "updated_at": "2021-03-16T18:38:01.942282Z",
      "submitted_at": "2021-03-16T18:38:01.937734Z",
      "symbol": "AAPL",
      "qty": "1",
      "filled_qty": "0",
      "order_class": "simple",
      "type": "market",
      "side": "buy",
      "time_in_force": "day",
      "status": "accepted",
      "extended_hours": false
    }
    """
    reqmock.patch(
        f"{BaseURL.TRADING_PAPER.value}/v2/orders/{order_id}",
        text=order_response,
    )

    trading_client.replace_order_by_id(
        order_id,
        PatchOrderRequest(
            qty="4",
            notional="750",
            advanced_instructions=AdvancedInstructions(display_qty="100"),
        ),
    )
    sent = reqmock.request_history[0].json()
    assert sent["qty"] == "4"
    assert sent["notional"] == "750"
    assert sent["advanced_instructions"]["display_qty"] == "100"

    trading_client.replace_order_by_id(order_id, ReplaceOrderRequest(qty=1))
    assert reqmock.request_history[1].json()["qty"] == 1
