from datetime import datetime
from typing import Dict, Iterator, List, Literal, Optional, Union, get_overloads, get_type_hints

import pytest

from alpaca.common.enums import PaginationType
from alpaca.common.types import RawData
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.models import BarSet, QuoteSet, TradeSet
from alpaca.data.requests import (
    CryptoBarsRequest,
    CryptoQuoteRequest,
    CryptoTradesRequest,
    OptionBarsRequest,
    OptionTradesRequest,
    StockBarsRequest,
    StockQuotesRequest,
    StockTradesRequest,
)
from alpaca.data.timeframe import TimeFrame

BAR = {"o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 100, "n": 10, "vw": 1.2}
QUOTE = {"ax": "V", "ap": 1.1, "as": 1, "bx": "V", "bp": 1.0, "bs": 2, "c": ["R"]}
TRADE = {"x": "V", "p": 1.0, "s": 5, "i": 7, "c": ["@"], "z": "C"}


def _items(template: dict, count: int, day: int) -> List[dict]:
    return [
        dict(template, t=f"2024-01-{day:02d}T14:{i // 60:02d}:{i % 60:02d}Z")
        for i in range(count)
    ]


def _serve_pages(
    reqmock, url: str, key: str, pages: List[Dict[str, List[dict]]]
) -> List[dict]:
    """Serves ``pages`` in order, chained by page tokens "p1", "p2", ...

    Returns a list that receives the query string of every request made.
    """
    seen: List[dict] = []

    def callback(request, context):
        qs = request.qs
        seen.append(qs)
        token = qs.get("page_token", [None])[0]
        index = 0 if token is None else int(token[1:])
        next_token = f"p{index + 1}" if index + 1 < len(pages) else None
        return {key: pages[index], "next_page_token": next_token}

    reqmock.get(url, json=callback)
    return seen


def test_iterator_is_lazy_and_yields_one_barset_per_page(
    reqmock, stock_client: StockHistoricalDataClient
):
    seen = _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/bars",
        "bars",
        [
            {"AAPL": _items(BAR, 3, 2), "MSFT": _items(BAR, 1, 2)},
            {"MSFT": _items(BAR, 2, 3)},
            {"AAPL": _items(BAR, 1, 4)},
        ],
    )
    request = StockBarsRequest(
        symbol_or_symbols=["AAPL", "MSFT"],
        timeframe=TimeFrame.Minute,
        start=datetime(2024, 1, 2),
    )

    pages = stock_client.get_stock_bars(
        request, handle_pagination=PaginationType.ITERATOR
    )

    # nothing is requested until the caller starts iterating
    assert reqmock.call_count == 0

    first = next(pages)
    assert isinstance(first, BarSet)
    assert reqmock.call_count == 1
    assert len(first["AAPL"]) == 3
    assert len(first["MSFT"]) == 1
    assert first.next_page_token == "p1"

    rest = list(pages)
    assert [p.next_page_token for p in rest] == ["p2", None]
    assert "AAPL" not in rest[0]
    assert len(rest[0]["MSFT"]) == 2
    assert rest[1]["AAPL"][0].timestamp.day == 4

    # each request continues from the previous page's token
    assert "page_token" not in seen[0]
    assert [qs["page_token"][0] for qs in seen[1:]] == ["p1", "p2"]
    assert reqmock.call_count == 3


def test_iterator_pages_add_up_to_full_result(
    reqmock, stock_client: StockHistoricalDataClient
):
    pages = [
        {"AAPL": _items(BAR, 3, 2), "MSFT": _items(BAR, 1, 2)},
        {"MSFT": _items(BAR, 2, 3)},
    ]
    _serve_pages(reqmock, "https://data.alpaca.markets/v2/stocks/bars", "bars", pages)

    def request():
        return StockBarsRequest(
            symbol_or_symbols=["AAPL", "MSFT"], timeframe=TimeFrame.Minute
        )

    full = stock_client.get_stock_bars(request())
    iterated = list(
        stock_client.get_stock_bars(
            request(), handle_pagination=PaginationType.ITERATOR
        )
    )

    assert isinstance(full, BarSet)
    assert full.next_page_token is None
    for symbol in ("AAPL", "MSFT"):
        merged = [bar for page in iterated if symbol in page for bar in page[symbol]]
        assert merged == full[symbol]


def test_iterator_respects_limit_across_pages(
    reqmock, stock_client: StockHistoricalDataClient
):
    seen = _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/trades",
        "trades",
        [
            {"AAPL": _items(TRADE, 4, 2)},
            {"AAPL": _items(TRADE, 2, 3)},
            {"AAPL": _items(TRADE, 1, 4)},
            {"AAPL": _items(TRADE, 1, 5)},
        ],
    )
    request = StockTradesRequest(symbol_or_symbols="AAPL", limit=7)

    pages = list(
        stock_client.get_stock_trades(
            request, handle_pagination=PaginationType.ITERATOR
        )
    )

    # each request asks only for what is still missing, and the 4th page is never requested
    assert [len(p["AAPL"]) for p in pages] == [4, 2, 1]
    assert [qs["limit"][0] for qs in seen] == ["7", "3", "1"]


def test_iterator_stops_when_limit_is_reached(
    reqmock, stock_client: StockHistoricalDataClient
):
    _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/quotes",
        "quotes",
        [{"AAPL": _items(QUOTE, 5, 2)}, {"AAPL": _items(QUOTE, 5, 3)}],
    )
    request = StockQuotesRequest(symbol_or_symbols="AAPL", limit=5)

    pages = list(
        stock_client.get_stock_quotes(
            request, handle_pagination=PaginationType.ITERATOR
        )
    )

    # the first page already holds `limit` items, so the second is never requested
    assert len(pages) == 1
    assert isinstance(pages[0], QuoteSet)
    assert pages[0].next_page_token == "p1"
    assert reqmock.call_count == 1


def test_none_returns_one_page_that_can_be_resumed(
    reqmock, stock_client: StockHistoricalDataClient
):
    seen = _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/bars",
        "bars",
        [{"AAPL": _items(BAR, 2, 2)}, {"AAPL": _items(BAR, 1, 3)}],
    )

    first = stock_client.get_stock_bars(
        StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day),
        handle_pagination=PaginationType.NONE,
    )
    assert isinstance(first, BarSet)
    assert len(first["AAPL"]) == 2
    assert first.next_page_token == "p1"
    assert reqmock.call_count == 1

    second = stock_client.get_stock_bars(
        StockBarsRequest(
            symbol_or_symbols="AAPL",
            timeframe=TimeFrame.Day,
            page_token=first.next_page_token,
        ),
        handle_pagination=PaginationType.NONE,
    )
    assert len(second["AAPL"]) == 1
    assert second.next_page_token is None
    assert seen[1]["page_token"] == ["p1"]


def test_full_pagination_can_resume_from_page_token(
    reqmock, stock_client: StockHistoricalDataClient
):
    seen = _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/bars",
        "bars",
        [
            {"AAPL": _items(BAR, 2, 2)},
            {"AAPL": _items(BAR, 1, 3)},
            {"AAPL": _items(BAR, 1, 4)},
        ],
    )

    rest = stock_client.get_stock_bars(
        StockBarsRequest(
            symbol_or_symbols="AAPL", timeframe=TimeFrame.Day, page_token="p1"
        )
    )

    assert [bar.timestamp.day for bar in rest["AAPL"]] == [3, 4]
    assert seen[0]["page_token"] == ["p1"]


def test_none_on_empty_response_returns_empty_page(
    reqmock, stock_client: StockHistoricalDataClient
):
    reqmock.get(
        "https://data.alpaca.markets/v2/stocks/bars",
        text='{"bars": {}, "next_page_token": null}',
    )

    page = stock_client.get_stock_bars(
        StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day),
        handle_pagination=PaginationType.NONE,
    )

    assert isinstance(page, BarSet)
    assert page.data == {}
    assert page.next_page_token is None


def test_raw_iterator_yields_api_pages(reqmock, raw_stock_client):
    _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/bars",
        "bars",
        [{"AAPL": _items(BAR, 2, 2)}, {"AAPL": _items(BAR, 1, 3)}],
    )
    request = StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day)

    pages = list(
        raw_stock_client.get_stock_bars(
            request, handle_pagination=PaginationType.ITERATOR
        )
    )

    assert [type(p) for p in pages] == [dict, dict]
    assert [p["next_page_token"] for p in pages] == ["p1", None]
    assert len(pages[0]["bars"]["AAPL"]) == 2

    # FULL in raw mode keeps returning the merged, symbol keyed dict
    merged = raw_stock_client.get_stock_bars(
        StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day)
    )
    assert list(merged) == ["AAPL"]
    assert len(merged["AAPL"]) == 3


def test_raw_iterator_continues_when_caller_mutates_a_page(reqmock, raw_stock_client):
    _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/bars",
        "bars",
        [
            {"AAPL": _items(BAR, 1, 2)},
            {"AAPL": _items(BAR, 1, 3)},
            {"AAPL": _items(BAR, 1, 4)},
        ],
    )
    pages = raw_stock_client.get_stock_bars(
        StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day),
        handle_pagination=PaginationType.ITERATOR,
    )

    # e.g. a caller checkpointing the token by popping it off each page
    tokens = [page.pop("next_page_token") for page in pages]

    assert tokens == ["p1", "p2", None]


def test_iterator_pages_have_working_df(
    reqmock, stock_client: StockHistoricalDataClient
):
    _serve_pages(
        reqmock,
        "https://data.alpaca.markets/v2/stocks/bars",
        "bars",
        [{"AAPL": _items(BAR, 2, 2)}, {"AAPL": _items(BAR, 1, 3)}],
    )
    pages = stock_client.get_stock_bars(
        StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day),
        handle_pagination=PaginationType.ITERATOR,
    )

    frames = [page.df for page in pages]

    assert [len(df) for df in frames] == [2, 1]
    assert "next_page_token" not in frames[0].columns
    assert frames[0].index.names == ["symbol", "timestamp"]


def test_invalid_pagination_type_raises(stock_client: StockHistoricalDataClient):
    with pytest.raises(ValueError):
        stock_client.get_stock_bars(
            StockBarsRequest(symbol_or_symbols="AAPL", timeframe=TimeFrame.Day),
            handle_pagination="pages",
        )


@pytest.mark.parametrize(
    "client_type, method, request_factory, url, key, template, set_type",
    [
        (
            CryptoHistoricalDataClient,
            "get_crypto_bars",
            lambda: CryptoBarsRequest(
                symbol_or_symbols="BTC/USD", timeframe=TimeFrame.Minute
            ),
            "https://data.alpaca.markets/v1beta3/crypto/us/bars",
            "bars",
            BAR,
            BarSet,
        ),
        (
            CryptoHistoricalDataClient,
            "get_crypto_quotes",
            lambda: CryptoQuoteRequest(symbol_or_symbols="BTC/USD"),
            "https://data.alpaca.markets/v1beta3/crypto/us/quotes",
            "quotes",
            QUOTE,
            QuoteSet,
        ),
        (
            CryptoHistoricalDataClient,
            "get_crypto_trades",
            lambda: CryptoTradesRequest(symbol_or_symbols="BTC/USD"),
            "https://data.alpaca.markets/v1beta3/crypto/us/trades",
            "trades",
            TRADE,
            TradeSet,
        ),
        (
            OptionHistoricalDataClient,
            "get_option_bars",
            lambda: OptionBarsRequest(
                symbol_or_symbols="AAPL240119C00100000", timeframe=TimeFrame.Hour
            ),
            "https://data.alpaca.markets/v1beta1/options/bars",
            "bars",
            BAR,
            BarSet,
        ),
        (
            OptionHistoricalDataClient,
            "get_option_trades",
            lambda: OptionTradesRequest(symbol_or_symbols="AAPL240119C00100000"),
            "https://data.alpaca.markets/v1beta1/options/trades",
            "trades",
            TRADE,
            TradeSet,
        ),
    ],
)
def test_crypto_and_option_time_series_support_iteration(
    reqmock, client_type, method, request_factory, url, key, template, set_type
):
    symbol = request_factory().symbol_or_symbols
    seen = _serve_pages(
        reqmock,
        url,
        key,
        [{symbol: _items(template, 2, 2)}, {symbol: _items(template, 1, 3)}],
    )
    client = client_type("key-id", "secret-key")

    pages = list(
        getattr(client, method)(
            request_factory(), handle_pagination=PaginationType.ITERATOR
        )
    )

    assert [type(p) for p in pages] == [set_type, set_type]
    assert [len(p[symbol]) for p in pages] == [2, 1]
    assert [p.next_page_token for p in pages] == ["p1", None]
    assert seen[1]["page_token"] == ["p1"]

    single = getattr(client, method)(
        request_factory(), handle_pagination=PaginationType.NONE
    )
    assert len(single[symbol]) == 2
    assert single.next_page_token == "p1"


def _unpaged(page):
    return Union[page, RawData]


def _paged(page):
    return Union[page, RawData, Iterator[Union[page, RawData]]]


@pytest.mark.parametrize(
    ("method", "page", "iterator_stubs"),
    [
        (StockHistoricalDataClient.get_stock_bars, BarSet, 1),
        (StockHistoricalDataClient.get_stock_quotes, QuoteSet, 1),
        (StockHistoricalDataClient.get_stock_trades, TradeSet, 1),
        (CryptoHistoricalDataClient.get_crypto_bars, BarSet, 2),
        (CryptoHistoricalDataClient.get_crypto_quotes, QuoteSet, 2),
        (CryptoHistoricalDataClient.get_crypto_trades, TradeSet, 2),
        (OptionHistoricalDataClient.get_option_bars, BarSet, 1),
        (OptionHistoricalDataClient.get_option_trades, TradeSet, 1),
    ],
)
def test_pagination_overloads_keep_the_previous_return(method, page, iterator_stubs):
    """A call that omits handle_pagination still sees the pre-pagination return type."""
    hints = [get_type_hints(stub) for stub in get_overloads(method)]
    iterator_return = Iterator[Union[page, RawData]]
    assert [hint["return"] for hint in hints[:iterator_stubs]] == [
        iterator_return
    ] * iterator_stubs
    assert hints[iterator_stubs]["return"] == _unpaged(page)
    assert hints[-1]["return"] == _paged(page)
    assert hints[0]["handle_pagination"] == Literal[PaginationType.ITERATOR]
    assert hints[iterator_stubs]["handle_pagination"] == Union[
        Literal[PaginationType.FULL, PaginationType.NONE], None
    ]
    assert hints[-1]["handle_pagination"] == Optional[PaginationType]
