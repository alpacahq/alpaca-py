from datetime import date
from urllib.parse import parse_qs, urlparse

from alpaca.common.enums import Sort, SupportedCurrencies
from alpaca.data._generated.models import (
    StockAuctionsResp,
    StockAuctionsRespSingle,
    StockBarsRespSingle,
    StockLatestBarsRespSingle,
    StockLatestQuotesRespSingle,
    StockLatestTradesRespSingle,
    StockQuotesRespSingle,
    StockSnapshotsRespSingle,
    StockTradesRespSingle,
)
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockAuctionsForSymbolRequest,
    StockAuctionsRequest,
    StockBarsForSymbolRequest,
    StockLatestBarForSymbolRequest,
    StockLatestQuoteForSymbolRequest,
    StockLatestTradeForSymbolRequest,
    StockQuotesForSymbolRequest,
    StockSnapshotForSymbolRequest,
    StockTradesForSymbolRequest,
)
from alpaca.data.timeframe import TimeFrame

_BAR = {
    "c": 178.21,
    "h": 178.26,
    "l": 178.21,
    "n": 65,
    "o": 178.26,
    "t": "2022-01-03T09:00:00Z",
    "v": 1118,
    "vw": 178.235733,
}
_QUOTE = {
    "ap": 178.8,
    "as": 4,
    "ax": "Q",
    "bp": 177.92,
    "bs": 4,
    "bx": "Q",
    "c": ["R"],
    "t": "2022-01-03T09:00:00Z",
    "z": "C",
}
_TRADE = {
    "c": ["@", "T"],
    "i": 689,
    "p": 172.6,
    "s": 100,
    "t": "2022-08-17T09:53:16Z",
    "x": "P",
    "z": "C",
}
_AUCTION = {
    "c": [{"c": "M", "p": 221.7, "t": "2022-10-13T20:00:00Z", "x": "P"}],
    "d": "2022-10-13",
    "o": [{"c": "O", "p": 208.49, "t": "2022-10-13T13:30:01Z", "x": "Q"}],
}


def _request_url(reqmock):
    # requests_mock lowercases Request.path and Request.qs. The prepared URL does not.
    return urlparse(reqmock.request_history[0].url)


def _path(reqmock) -> str:
    return _request_url(reqmock).path


def _query(reqmock) -> dict:
    return parse_qs(_request_url(reqmock).query)


def test_get_stock_bars_for_symbol(reqmock, stock_client: StockHistoricalDataClient):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/bars",
        json={
            "bars": [_BAR],
            "currency": "USD",
            "next_page_token": "token-2",
            "symbol": "AAPL",
        },
    )

    page = stock_client.get_stock_bars_for_symbol(
        StockBarsForSymbolRequest(
            symbol="AAPL",
            timeframe=TimeFrame.Day,
            adjustment=Adjustment.SPLIT,
            sort=Sort.ASC,
            page_token="token-1",
            limit=1,
        )
    )

    assert isinstance(page, StockBarsRespSingle)
    assert page.symbol == "AAPL"
    assert page.currency == "USD"
    assert page.next_page_token == "token-2"
    assert page.bars[0].c == 178.21
    assert _path(reqmock) == "/v2/stocks/AAPL/bars"
    query = _query(reqmock)
    assert "symbols" not in query
    assert query["timeframe"] == ["1Day"]
    assert query["adjustment"] == ["split"]
    assert query["page_token"] == ["token-1"]
    assert reqmock.called_once


def test_get_stock_bars_for_symbol_raw_data_keeps_symbol(
    reqmock, raw_stock_client: StockHistoricalDataClient
):
    body = {
        "bars": [_BAR],
        "currency": "USD",
        "next_page_token": "token-2",
        "symbol": "AAPL",
    }
    reqmock.get("https://data.alpaca.markets/v2/stocks/AAPL/bars", json=body)

    page = raw_stock_client.get_stock_bars_for_symbol(
        StockBarsForSymbolRequest(symbol="AAPL", timeframe=TimeFrame.Day)
    )

    assert page["symbol"] == "AAPL"
    assert page["currency"] == "USD"
    assert page["next_page_token"] == "token-2"
    assert page["bars"][0]["c"] == 178.21
    assert _path(reqmock) == "/v2/stocks/AAPL/bars"
    assert "symbols" not in reqmock.request_history[0].qs
    assert reqmock.called_once


def test_get_stock_quotes_for_symbol(reqmock, stock_client: StockHistoricalDataClient):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/quotes",
        json={
            "quotes": [_QUOTE],
            "currency": "USD",
            "next_page_token": None,
            "symbol": "AAPL",
        },
    )

    page = stock_client.get_stock_quotes_for_symbol(
        StockQuotesForSymbolRequest(symbol="AAPL", feed=DataFeed.IEX)
    )

    assert isinstance(page, StockQuotesRespSingle)
    assert page.symbol == "AAPL"
    assert page.quotes[0].ap == 178.8
    assert _path(reqmock) == "/v2/stocks/AAPL/quotes"
    query = _query(reqmock)
    assert "symbols" not in query
    assert query["feed"] == ["iex"]


def test_get_stock_trades_for_symbol(reqmock, stock_client: StockHistoricalDataClient):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/trades",
        json={
            "trades": [_TRADE],
            "currency": "USD",
            "next_page_token": None,
            "symbol": "AAPL",
        },
    )

    page = stock_client.get_stock_trades_for_symbol(
        StockTradesForSymbolRequest(symbol="AAPL")
    )

    assert isinstance(page, StockTradesRespSingle)
    assert page.symbol == "AAPL"
    assert page.trades[0].p == 172.6
    assert _path(reqmock) == "/v2/stocks/AAPL/trades"
    assert "symbols" not in reqmock.request_history[0].qs


def test_get_stock_latest_bar_for_symbol(
    reqmock, stock_client: StockHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/bars/latest",
        json={"bar": _BAR, "currency": "USD", "symbol": "AAPL"},
    )

    page = stock_client.get_stock_latest_bar_for_symbol(
        StockLatestBarForSymbolRequest(symbol="AAPL", currency=SupportedCurrencies.USD)
    )

    assert isinstance(page, StockLatestBarsRespSingle)
    assert page.symbol == "AAPL"
    assert page.bar.c == 178.21
    assert "bars" not in StockLatestBarsRespSingle.model_fields
    assert _path(reqmock) == "/v2/stocks/AAPL/bars/latest"
    query = _query(reqmock)
    assert "symbols" not in query
    assert query["currency"] == ["USD"]


def test_get_stock_latest_quote_for_symbol(
    reqmock, stock_client: StockHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/quotes/latest",
        json={"quote": _QUOTE, "currency": "USD", "symbol": "AAPL"},
    )

    page = stock_client.get_stock_latest_quote_for_symbol(
        StockLatestQuoteForSymbolRequest(symbol="AAPL")
    )

    assert isinstance(page, StockLatestQuotesRespSingle)
    assert page.symbol == "AAPL"
    assert page.quote.bp == 177.92
    assert _path(reqmock) == "/v2/stocks/AAPL/quotes/latest"
    assert "symbols" not in reqmock.request_history[0].qs


def test_get_stock_latest_trade_for_symbol(
    reqmock, stock_client: StockHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/trades/latest",
        json={"trade": _TRADE, "currency": "USD", "symbol": "AAPL"},
    )

    page = stock_client.get_stock_latest_trade_for_symbol(
        StockLatestTradeForSymbolRequest(symbol="AAPL")
    )

    assert isinstance(page, StockLatestTradesRespSingle)
    assert page.symbol == "AAPL"
    assert page.trade.s == 100
    assert _path(reqmock) == "/v2/stocks/AAPL/trades/latest"
    assert "symbols" not in reqmock.request_history[0].qs


def test_get_stock_snapshot_for_symbol(
    reqmock, stock_client: StockHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/AAPL/snapshot",
        json={"dailyBar": _BAR, "symbol": "AAPL", "currency": "USD"},
    )

    page = stock_client.get_stock_snapshot_for_symbol(
        StockSnapshotForSymbolRequest(symbol="AAPL")
    )

    assert isinstance(page, StockSnapshotsRespSingle)
    assert page.symbol == "AAPL"
    assert page.daily_bar.c == 178.21
    assert _path(reqmock) == "/v2/stocks/AAPL/snapshot"
    assert "symbols" not in reqmock.request_history[0].qs


def test_get_stock_auctions(reqmock, stock_client: StockHistoricalDataClient):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/auctions",
        json={
            "auctions": {"AAPL": [_AUCTION], "TSLA": [_AUCTION]},
            "currency": "USD",
            "next_page_token": None,
        },
    )

    page = stock_client.get_stock_auctions(
        StockAuctionsRequest(symbol_or_symbols=["AAPL", "TSLA"])
    )

    assert isinstance(page, StockAuctionsResp)
    assert page.currency == "USD"
    assert page.auctions["AAPL"][0].d == date(2022, 10, 13)
    assert _path(reqmock) == "/v2/stocks/auctions"
    assert _query(reqmock)["symbols"] == ["AAPL,TSLA"]


def test_get_stock_auctions_for_symbol(
    reqmock, stock_client: StockHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/TSLA/auctions",
        json={
            "auctions": [_AUCTION],
            "currency": "USD",
            "next_page_token": None,
            "symbol": "TSLA",
        },
    )

    page = stock_client.get_stock_auctions_for_symbol(
        StockAuctionsForSymbolRequest(symbol="TSLA")
    )

    assert isinstance(page, StockAuctionsRespSingle)
    assert page.symbol == "TSLA"
    assert page.auctions[0].d == date(2022, 10, 13)
    assert _path(reqmock) == "/v2/stocks/TSLA/auctions"
    assert "symbols" not in reqmock.request_history[0].qs


def test_get_stock_condition_codes(reqmock, stock_client: StockHistoricalDataClient):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/meta/conditions/trade",
        json={"@": "Regular Sale"},
    )

    codes = stock_client.get_stock_condition_codes("trade", "A")

    assert codes == {"@": "Regular Sale"}
    assert _path(reqmock) == "/v2/stocks/meta/conditions/trade"
    assert _query(reqmock)["tape"] == ["A"]


def test_get_stock_exchange_codes(reqmock, stock_client: StockHistoricalDataClient):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/meta/exchanges",
        json={"Q": "NASDAQ"},
    )

    codes = stock_client.get_stock_exchange_codes()

    assert codes == {"Q": "NASDAQ"}
    assert _path(reqmock) == "/v2/stocks/meta/exchanges"
    assert _query(reqmock) == {}
