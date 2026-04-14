import os
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

import boto3

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    TrailingStopOrderRequest,
    GetOrdersRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.trading.models import Clock
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

NY_TZ = ZoneInfo("America/New_York")

_clients_cache = None


def _get_clients() -> tuple[TradingClient, StockHistoricalDataClient]:
    global _clients_cache
    if _clients_cache is not None:
        return _clients_cache
    ssm = boto3.client("ssm")
    api_key = ssm.get_parameter(Name="/alpaca/ALPACA_API_KEY", WithDecryption=True)["Parameter"]["Value"]
    secret_key = ssm.get_parameter(Name="/alpaca/ALPACA_SECRET_KEY", WithDecryption=True)["Parameter"]["Value"]
    paper = os.environ.get("ALPACA_PAPER_TRADE", "true").lower() != "false"
    trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
    stock_historical_data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
    _clients_cache = (trading_client, stock_historical_data_client)
    return _clients_cache


def get_clock() -> Clock:
    trading_client, _ = _get_clients()
    return trading_client.get_clock()


def get_price_history(symbol: str, bars: int = 120) -> list[dict]:
    _, stock_historical_data_client = _get_clients()
    today = datetime.now(NY_TZ).date()
    start = today - timedelta(days=180)   # ~6 months covers 120+ trading days
    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
    )
    response = stock_historical_data_client.get_stock_bars(req)
    bars_data = response[symbol] if symbol in response else []
    result = [
        {
            "close": float(bar.close),
            "high":  float(bar.high),    # needed for ATR calculation
            "low":   float(bar.low),     # needed for ATR calculation
            "datetime": bar.timestamp.timestamp() * 1000,
        }
        for bar in bars_data
    ]
    return result[-bars:] if len(result) > bars else result


def get_current_quotes(symbols: list[str]) -> dict:
    _, stock_historical_data_client = _get_clients()
    req = StockLatestQuoteRequest(symbol_or_symbols=symbols)
    response = stock_historical_data_client.get_stock_latest_quote(req)
    return {
        symbol: {"askPrice": float(quote.ask_price), "bidPrice": float(quote.bid_price)}
        for symbol, quote in response.items()
    }


def get_orders(account_hash=None):
    trading_client, _ = _get_clients()
    return trading_client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))


def cancel_order(account_hash, order_id: str) -> None:
    trading_client, _ = _get_clients()
    trading_client.cancel_order_by_id(order_id)


def place_order(account_hash, symbol: str, qty: int, side: str):
    trading_client, _ = _get_clients()
    # Validate side parameter explicitly to prevent silent conversion to SELL
    side_upper = side.upper() if isinstance(side, str) else ""
    if side_upper not in ("BUY", "SELL"):
        raise ValueError(f"Invalid order side '{side}': must be 'BUY' or 'SELL' (case-insensitive)")
    order_side = OrderSide.BUY if side_upper == "BUY" else OrderSide.SELL
    req = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=order_side,
        time_in_force=TimeInForce.DAY,
    )
    return trading_client.submit_order(req)


def place_trailing_stop_order(account_hash, symbol: str, qty: int, trail_percent: float, side: str):
    trading_client, _ = _get_clients()
    # Validate side parameter explicitly to prevent silent conversion to SELL
    side_upper = side.upper() if isinstance(side, str) else ""
    if side_upper not in ("BUY", "SELL"):
        raise ValueError(f"Invalid order side '{side}': must be 'BUY' or 'SELL' (case-insensitive)")
    order_side = OrderSide.BUY if side_upper == "BUY" else OrderSide.SELL
    req = TrailingStopOrderRequest(
        symbol=symbol,
        qty=qty,
        side=order_side,
        time_in_force=TimeInForce.GTC,
        trail_percent=trail_percent,
    )
    return trading_client.submit_order(req)


def get_account():
    trading_client, _ = _get_clients()
    return trading_client.get_account()


def get_all_positions():
    trading_client, _ = _get_clients()
    return trading_client.get_all_positions()
