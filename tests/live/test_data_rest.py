"""Read-only live market data smoke tests."""

from datetime import datetime, timedelta, timezone

import pytest

from alpaca.data.requests import (
    CryptoLatestQuoteRequest,
    NewsRequest,
    StockBarsRequest,
    StockLatestQuoteRequest,
)
from alpaca.data.timeframe import TimeFrame


@pytest.mark.live
def test_get_stock_latest_quote(stock_client_live, live_call):
    quote = live_call(
        "get_stock_latest_quote",
        stock_client_live.get_stock_latest_quote,
        StockLatestQuoteRequest(symbol_or_symbols="AAPL"),
    )
    assert quote is not None


@pytest.mark.live
def test_get_stock_bars(stock_client_live, live_call):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=5)
    bars = live_call(
        "get_stock_bars",
        stock_client_live.get_stock_bars,
        StockBarsRequest(
            symbol_or_symbols="AAPL",
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            limit=5,
        ),
    )
    assert bars is not None


@pytest.mark.live
def test_get_crypto_latest_quote(crypto_client_live, live_call):
    quote = live_call(
        "get_crypto_latest_quote",
        crypto_client_live.get_crypto_latest_quote,
        CryptoLatestQuoteRequest(symbol_or_symbols="BTC/USD"),
    )
    assert quote is not None


@pytest.mark.live
def test_get_news(news_client_live, live_call):
    news = live_call(
        "get_news",
        news_client_live.get_news,
        NewsRequest(symbols="AAPL", limit=3),
    )
    assert news is not None
