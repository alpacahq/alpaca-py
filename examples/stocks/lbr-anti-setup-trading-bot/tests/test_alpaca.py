from unittest.mock import MagicMock
from datetime import datetime, timezone

import pytest

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, TrailingStopOrderRequest

import alpaca_broker


def _make_mock_clients(mocker):
    mock_trading = MagicMock()
    mock_data = MagicMock()
    mocker.patch("alpaca_broker._get_clients", return_value=(mock_trading, mock_data))
    return mock_trading, mock_data


def test_get_price_history_returns_correct_shape(mocker):
    mock_trading, mock_data = _make_mock_clients(mocker)
    ts = datetime(2024, 1, 2, 10, 0, tzinfo=timezone.utc)
    bar = MagicMock(close=150.0, timestamp=ts)
    mock_data.get_stock_bars.return_value = {"AAPL": [bar]}

    result = alpaca_broker.get_price_history("AAPL", bars=500)

    assert len(result) == 1
    assert result[0]["close"] == 150.0
    assert isinstance(result[0]["datetime"], float)


def test_place_market_order_buy(mocker):
    mock_trading, _ = _make_mock_clients(mocker)
    mock_order = MagicMock()
    mock_trading.submit_order.return_value = mock_order

    result = alpaca_broker.place_market_order(None, "AAPL", 10, "BUY")

    mock_trading.submit_order.assert_called_once()
    call_arg = mock_trading.submit_order.call_args[0][0]
    assert isinstance(call_arg, MarketOrderRequest)
    assert call_arg.symbol == "AAPL"
    assert call_arg.qty == 10
    assert call_arg.side == OrderSide.BUY
    assert call_arg.time_in_force == TimeInForce.DAY
    assert result is mock_order


def test_place_market_order_sell(mocker):
    mock_trading, _ = _make_mock_clients(mocker)
    mock_trading.submit_order.return_value = MagicMock()

    alpaca_broker.place_market_order(None, "MSFT", 5, "SELL")

    call_arg = mock_trading.submit_order.call_args[0][0]
    assert call_arg.side == OrderSide.SELL


def test_place_market_order_rejects_invalid_side(mocker):
    mock_trading, _ = _make_mock_clients(mocker)

    with pytest.raises(ValueError, match="Invalid order side"):
        alpaca_broker.place_market_order(None, "MSFT", 5, "HOLD")

    mock_trading.submit_order.assert_not_called()


def test_place_trailing_stop_order(mocker):
    mock_trading, _ = _make_mock_clients(mocker)
    mock_trading.submit_order.return_value = MagicMock()

    alpaca_broker.place_trailing_stop_order(None, "NVDA", 3, 4.75, "SELL")

    call_arg = mock_trading.submit_order.call_args[0][0]
    assert isinstance(call_arg, TrailingStopOrderRequest)
    assert call_arg.trail_percent == 4.75
    assert call_arg.time_in_force == TimeInForce.GTC


def test_get_clock_returns_clock(mocker):
    mock_trading, _ = _make_mock_clients(mocker)
    mock_clock = MagicMock(is_open=True)
    mock_trading.get_clock.return_value = mock_clock

    result = alpaca_broker.get_clock()

    assert result is mock_clock
    assert result.is_open is True


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on", "t", "y"])
def test_parse_bool_env_truthy(monkeypatch, value):
    monkeypatch.setenv("ALPACA_PAPER_TRADE", value)

    assert alpaca_broker._parse_bool_env("ALPACA_PAPER_TRADE", default=False) is True


@pytest.mark.parametrize("value", ["false", "False", "0", "no", "off", "f", "n"])
def test_parse_bool_env_falsy(monkeypatch, value):
    monkeypatch.setenv("ALPACA_PAPER_TRADE", value)

    assert alpaca_broker._parse_bool_env("ALPACA_PAPER_TRADE", default=True) is False


def test_parse_bool_env_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("ALPACA_PAPER_TRADE", raising=False)

    assert alpaca_broker._parse_bool_env("ALPACA_PAPER_TRADE", default=True) is True
    assert alpaca_broker._parse_bool_env("ALPACA_PAPER_TRADE", default=False) is False


def test_parse_bool_env_rejects_invalid_value(monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_TRADE", "paper")

    with pytest.raises(ValueError, match="Invalid boolean value"):
        alpaca_broker._parse_bool_env("ALPACA_PAPER_TRADE", default=True)


def test_get_clients_logs_resolved_trading_mode(mocker, monkeypatch, caplog):
    alpaca_broker._clients_cache = None
    monkeypatch.setenv("ALPACA_PAPER_TRADE", "0")
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.side_effect = [
        {"Parameter": {"Value": "key"}},
        {"Parameter": {"Value": "secret"}},
    ]
    mocker.patch("alpaca_broker.boto3.client", return_value=mock_ssm)
    mock_trading_client = mocker.patch("alpaca_broker.TradingClient")
    mock_data_client = mocker.patch("alpaca_broker.StockHistoricalDataClient")

    with caplog.at_level("INFO"):
        alpaca_broker._get_clients()

    mock_trading_client.assert_called_once_with(api_key="key", secret_key="secret", paper=False)
    mock_data_client.assert_called_once_with(api_key="key", secret_key="secret")
    assert "Resolved Alpaca trading mode: live" in caplog.text
    assert "secret" not in caplog.text
    alpaca_broker._clients_cache = None
