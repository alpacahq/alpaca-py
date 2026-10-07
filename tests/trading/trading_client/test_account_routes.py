import json
from alpaca.common.enums import BaseURL
from alpaca.trading.models import TradeAccount, AccountConfiguration
from alpaca.trading.client import TradingClient
from requests_mock import Mocker


def test_get_account(reqmock: Mocker, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account",
        text="""
        {
          "account_blocked": false,
          "accrued_fees": "0",
          "account_number": "010203ABCD",
          "buying_power": "262113.632",
          "cash": "-23140.2",
          "created_at": "2019-06-12T22:47:07.99658Z",
          "currency": "USD",
          "daytrade_count": 0,
          "daytrading_buying_power": "262113.632",
          "equity": "103820.56",
          "id": "e6fe16f3-64a4-4921-8928-cadf02f92f98",
          "initial_margin": "63480.38",
          "last_equity": "103529.24",
          "last_maintenance_margin": "38000.832",
          "non_marginable_buying_power": "98945.02",
          "long_market_value": "126960.76",
          "maintenance_margin": "38088.228",
          "multiplier": "4",
          "pattern_day_trader": false,
          "portfolio_value": "103820.56",
          "regt_buying_power": "80680.36",
          "short_market_value": "0",
          "shorting_enabled": true,
          "sma": "0",
          "status": "ACTIVE",
          "trade_suspended_by_user": false,
          "trading_blocked": false,
          "transfers_blocked": false,
          "options_buying_power": "262113.632",
          "options_approved_level": "1",
          "options_trading_level": "1"
        }
      """,
    )

    account = trading_client.get_account()

    assert reqmock.called_once
    assert isinstance(account, TradeAccount)
    assert account.options_buying_power == "262113.632"
    assert account.options_approved_level == 1
    assert account.options_trading_level == 1


def test_get_account_configurations(reqmock: Mocker, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/configurations",
        text="""
        {
          "dtbp_check": "entry",
          "no_shorting": false,
          "suspend_trade": false,
          "fractional_trading": true,
          "max_margin_multiplier": "4",
          "pdt_check": "entry",
          "trade_confirm_email": "all",
          "ptp_no_exception_entry": false,
          "max_options_trading_level": 1
        }
      """,
    )

    account_configurations = trading_client.get_account_configurations()
    assert reqmock.called_once
    assert isinstance(account_configurations, AccountConfiguration)
    assert account_configurations.max_options_trading_level == 1


def test_get_account_configurations_without_deprecated_pdt_fields(
    reqmock: Mocker, trading_client: TradingClient
):
    """dtbp_check / pdt_check are removed from Alpaca responses on 2026-07-06
    (FINRA intraday-margin migration). The config model must still validate when
    they are absent, defaulting them to None instead of raising a ValidationError."""
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/configurations",
        text="""
        {
          "no_shorting": false,
          "suspend_trade": false,
          "fractional_trading": true,
          "max_margin_multiplier": "4",
          "trade_confirm_email": "all",
          "ptp_no_exception_entry": false,
          "max_options_trading_level": 1
        }
      """,
    )

    account_configurations = trading_client.get_account_configurations()
    assert reqmock.called_once
    assert isinstance(account_configurations, AccountConfiguration)
    assert account_configurations.dtbp_check is None
    assert account_configurations.pdt_check is None


def test_set_account_configurations(reqmock: Mocker, trading_client: TradingClient):
    new_account_configurations = AccountConfiguration(
        **{
            "dtbp_check": "entry",
            "no_shorting": True,
            "suspend_trade": False,
            "fractional_trading": True,
            "max_margin_multiplier": "1",
            "pdt_check": "both",
            "trade_confirm_email": "all",
            "ptp_no_exception_entry": False,
            "max_options_trading_level": 1,
        }
    )
    reqmock.patch(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/configurations",
        json=new_account_configurations.model_dump(),
    )

    account_configurations = trading_client.set_account_configurations(
        new_account_configurations
    )
    assert reqmock.called_once
    assert isinstance(account_configurations, AccountConfiguration)
    assert new_account_configurations == account_configurations


def test_set_account_configurations_disable_overnight_trading_request_body(
    reqmock: Mocker, trading_client: TradingClient
):
    """Unset disable_overnight_trading stays out of the PATCH body. Explicit
    True and False are sent."""
    reqmock.patch(
        f"{BaseURL.TRADING_PAPER.value}/v2/account/configurations",
        text="""
        {
          "dtbp_check": "entry",
          "no_shorting": false,
          "suspend_trade": false,
          "fractional_trading": true,
          "max_margin_multiplier": "4",
          "pdt_check": "entry",
          "trade_confirm_email": "all",
          "ptp_no_exception_entry": false
        }
        """,
    )

    base = {
        "dtbp_check": "entry",
        "no_shorting": False,
        "suspend_trade": False,
        "fractional_trading": True,
        "max_margin_multiplier": "4",
        "pdt_check": "entry",
        "trade_confirm_email": "all",
        "ptp_no_exception_entry": False,
    }

    trading_client.set_account_configurations(AccountConfiguration(**base))
    unset_body = reqmock.request_history[0].json()
    assert "disable_overnight_trading" not in unset_body

    trading_client.set_account_configurations(
        AccountConfiguration(**base, disable_overnight_trading=True)
    )
    assert reqmock.request_history[1].json()["disable_overnight_trading"] is True

    trading_client.set_account_configurations(
        AccountConfiguration(**base, disable_overnight_trading=False)
    )
    assert reqmock.request_history[2].json()["disable_overnight_trading"] is False
