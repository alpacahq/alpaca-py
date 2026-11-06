"""Static type-check fixture for the ``handle_pagination`` overloads.

This module is checked by mypy (``make typecheck``), never imported or collected by
pytest: the functions below are only type-checked, not executed. ``assert_type``
fails the mypy run when a call resolves to a different return type than expected,
so a later signature change cannot silently widen the default-call return type.

Run with ``--warn-unused-ignores`` so the ``type: ignore`` comments below also fail
when the call they cover stops being a type error.
"""

from typing import Any, Dict, Iterator, Optional, Union

from typing_extensions import assert_type

from alpaca.common.enums import PaginationType
from alpaca.data.enums import CryptoFeed
from alpaca.data.historical import (
    CryptoHistoricalDataClient,
    OptionHistoricalDataClient,
    StockHistoricalDataClient,
)
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

RawData = Dict[str, Any]


def stock_bars(
    client: StockHistoricalDataClient,
    request: StockBarsRequest,
    any_pagination: PaginationType,
    maybe_pagination: Optional[PaginationType],
) -> None:
    # Omitted, FULL and NONE are one set, so indexing by symbol type-checks.
    assert_type(client.get_stock_bars(request), Union[BarSet, RawData])
    assert_type(
        client.get_stock_bars(request, handle_pagination=PaginationType.FULL),
        Union[BarSet, RawData],
    )
    assert_type(
        client.get_stock_bars(request, PaginationType.NONE), Union[BarSet, RawData]
    )
    assert_type(client.get_stock_bars(request)["AAPL"], Any)

    # Only ITERATOR is an iterator.
    assert_type(
        client.get_stock_bars(request, handle_pagination=PaginationType.ITERATOR),
        Iterator[Union[BarSet, RawData]],
    )
    assert_type(
        client.get_stock_bars(request, PaginationType.ITERATOR),
        Iterator[Union[BarSet, RawData]],
    )
    client.get_stock_bars(request, handle_pagination=PaginationType.ITERATOR)[  # type: ignore[index]
        "AAPL"
    ]

    # A value only known as ``PaginationType`` could be any of them.
    assert_type(
        client.get_stock_bars(request, handle_pagination=any_pagination),
        Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]],
    )
    assert_type(
        client.get_stock_bars(request, handle_pagination=maybe_pagination),
        Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]],
    )


def stock_quotes_and_trades(
    client: StockHistoricalDataClient,
    quotes: StockQuotesRequest,
    trades: StockTradesRequest,
) -> None:
    assert_type(client.get_stock_quotes(quotes), Union[QuoteSet, RawData])
    assert_type(
        client.get_stock_quotes(quotes, PaginationType.NONE), Union[QuoteSet, RawData]
    )
    assert_type(
        client.get_stock_quotes(quotes, PaginationType.ITERATOR),
        Iterator[Union[QuoteSet, RawData]],
    )
    assert_type(client.get_stock_trades(trades), Union[TradeSet, RawData])
    assert_type(
        client.get_stock_trades(trades, PaginationType.FULL), Union[TradeSet, RawData]
    )
    assert_type(
        client.get_stock_trades(trades, PaginationType.ITERATOR),
        Iterator[Union[TradeSet, RawData]],
    )


def crypto_bars(
    client: CryptoHistoricalDataClient,
    request: CryptoBarsRequest,
    feed: CryptoFeed,
    any_pagination: PaginationType,
) -> None:
    # feed omitted, positional or keyword
    assert_type(client.get_crypto_bars(request), Union[BarSet, RawData])
    assert_type(client.get_crypto_bars(request, feed), Union[BarSet, RawData])
    assert_type(client.get_crypto_bars(request, feed=feed), Union[BarSet, RawData])
    assert_type(
        client.get_crypto_bars(request, feed, PaginationType.FULL),
        Union[BarSet, RawData],
    )
    assert_type(
        client.get_crypto_bars(request, handle_pagination=PaginationType.NONE),
        Union[BarSet, RawData],
    )
    assert_type(client.get_crypto_bars(request)["BTC/USD"], Any)

    assert_type(
        client.get_crypto_bars(request, handle_pagination=PaginationType.ITERATOR),
        Iterator[Union[BarSet, RawData]],
    )
    assert_type(
        client.get_crypto_bars(request, feed, PaginationType.ITERATOR),
        Iterator[Union[BarSet, RawData]],
    )
    assert_type(
        client.get_crypto_bars(
            request, feed=feed, handle_pagination=PaginationType.ITERATOR
        ),
        Iterator[Union[BarSet, RawData]],
    )
    assert_type(
        client.get_crypto_bars(request, handle_pagination=any_pagination),
        Union[BarSet, RawData, Iterator[Union[BarSet, RawData]]],
    )


def crypto_quotes_and_trades(
    client: CryptoHistoricalDataClient,
    quotes: CryptoQuoteRequest,
    trades: CryptoTradesRequest,
    feed: CryptoFeed,
) -> None:
    assert_type(client.get_crypto_quotes(quotes), Union[QuoteSet, RawData])
    assert_type(client.get_crypto_quotes(quotes, feed), Union[QuoteSet, RawData])
    assert_type(
        client.get_crypto_quotes(quotes, feed, PaginationType.ITERATOR),
        Iterator[Union[QuoteSet, RawData]],
    )
    assert_type(
        client.get_crypto_quotes(quotes, handle_pagination=PaginationType.ITERATOR),
        Iterator[Union[QuoteSet, RawData]],
    )
    assert_type(client.get_crypto_trades(trades), Union[TradeSet, RawData])
    assert_type(client.get_crypto_trades(trades, feed), Union[TradeSet, RawData])
    assert_type(
        client.get_crypto_trades(trades, feed, PaginationType.ITERATOR),
        Iterator[Union[TradeSet, RawData]],
    )
    assert_type(
        client.get_crypto_trades(trades, handle_pagination=PaginationType.ITERATOR),
        Iterator[Union[TradeSet, RawData]],
    )


def option_bars_and_trades(
    client: OptionHistoricalDataClient,
    bars: OptionBarsRequest,
    trades: OptionTradesRequest,
) -> None:
    assert_type(client.get_option_bars(bars), Union[BarSet, RawData])
    assert_type(
        client.get_option_bars(bars, PaginationType.NONE), Union[BarSet, RawData]
    )
    assert_type(
        client.get_option_bars(bars, PaginationType.ITERATOR),
        Iterator[Union[BarSet, RawData]],
    )
    assert_type(client.get_option_trades(trades), Union[TradeSet, RawData])
    assert_type(
        client.get_option_trades(trades, PaginationType.FULL), Union[TradeSet, RawData]
    )
    assert_type(
        client.get_option_trades(trades, PaginationType.ITERATOR),
        Iterator[Union[TradeSet, RawData]],
    )
