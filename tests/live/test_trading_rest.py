"""Read-only live TradingClient smoke tests (paper by default)."""

import pytest

from alpaca.trading.requests import GetOrdersRequest


@pytest.mark.live
def test_get_account(trading_client_live, live_call):
    account = live_call("get_account", trading_client_live.get_account)
    assert account is not None


@pytest.mark.live
def test_get_account_configurations(trading_client_live, live_call):
    config = live_call(
        "get_account_configurations", trading_client_live.get_account_configurations
    )
    assert config is not None


@pytest.mark.live
def test_get_clock(trading_client_live, live_call):
    clock = live_call("get_clock", trading_client_live.get_clock)
    assert clock is not None


@pytest.mark.live
def test_get_calendar(trading_client_live, live_call):
    calendar = live_call(
        "get_calendar",
        trading_client_live.get_calendar,
        response_transform=lambda c: c[:5] if isinstance(c, list) else c,
    )
    assert calendar is not None


@pytest.mark.live
def test_get_asset(trading_client_live, live_call):
    asset = live_call("get_asset", trading_client_live.get_asset, "AAPL")
    assert asset is not None


@pytest.mark.live
def test_get_all_positions(trading_client_live, live_call):
    positions = live_call("get_all_positions", trading_client_live.get_all_positions)
    assert positions is not None


@pytest.mark.live
def test_get_orders(trading_client_live, live_call):
    orders = live_call(
        "get_orders", trading_client_live.get_orders, GetOrdersRequest(limit=5)
    )
    assert orders is not None
