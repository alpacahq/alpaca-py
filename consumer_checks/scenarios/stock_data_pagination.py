"""Page-by-page market data (#877): not released yet, so ``since="0.46.0"``.

``handle_pagination=PaginationType.ITERATOR`` returns a lazy iterator of pages,
and ``PaginationType.NONE`` returns one page whose ``next_page_token`` the user
passes back as ``page_token``. Neither exists in the BASELINE release, so these
scenarios are recorded with this checkout's SDK until BASELINE reaches 0.46.0.

The pages are stubbed: the scenarios show exactly which requests the SDK makes
and which tokens it passes, whatever data the API has at the time.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from alpaca.common.enums import PaginationType
from alpaca.data.enums import DataFeed
from alpaca.data.models import BarSet
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from . import Context, scenario

SINCE = "0.46.0"


def _bar(day: int, price: float) -> Dict[str, Any]:
    return {
        "t": f"2024-03-0{day}T05:00:00Z",
        "o": price,
        "h": price + 2,
        "l": price - 1,
        "c": price + 1,
        "v": 1000,
        "n": 10,
        "vw": price + 0.5,
    }


FIRST_PAGE = {
    "status": 200,
    "json": {
        "bars": {"AAPL": [_bar(4, 175.0), _bar(5, 176.0)]},
        "next_page_token": "page-2",
    },
}
LAST_PAGE = {
    "status": 200,
    "json": {"bars": {"AAPL": [_bar(6, 177.0)]}, "next_page_token": None},
}


def _bars_request(page_token: Optional[str] = None) -> StockBarsRequest:
    return StockBarsRequest(
        symbol_or_symbols="AAPL",
        timeframe=TimeFrame.Day,
        start=datetime(2024, 3, 4, tzinfo=timezone.utc),
        end=datetime(2024, 3, 9, tzinfo=timezone.utc),
        feed=DataFeed.IEX,
        page_token=page_token,
    )


@scenario(
    covers=["StockHistoricalDataClient.get_stock_bars"],
    since=SINCE,
    stub_responses=[FIRST_PAGE, LAST_PAGE],
)
def bars_page_iterator(ctx: Context) -> Dict[str, Any]:
    pages = ctx.stock_data.get_stock_bars(
        _bars_request(), handle_pagination=PaginationType.ITERATOR
    )

    # A lazy iterator of BarSets, one per API page, not one merged BarSet.
    assert isinstance(pages, Iterator)
    first = next(pages)
    assert isinstance(first, BarSet)
    assert len(first["AAPL"]) == 2
    assert first.next_page_token == "page-2"
    rest = list(pages)
    assert len(rest) == 1
    last = rest[0]
    assert isinstance(last, BarSet)
    assert len(last["AAPL"]) == 1
    assert last.next_page_token is None
    return {"first": first, "last": last}


@scenario(
    covers=["StockHistoricalDataClient.get_stock_bars"],
    since=SINCE,
    stub_responses=[FIRST_PAGE, LAST_PAGE],
)
def bars_one_page_at_a_time(ctx: Context) -> Dict[str, Any]:
    first = ctx.stock_data.get_stock_bars(
        _bars_request(), handle_pagination=PaginationType.NONE
    )
    assert isinstance(first, BarSet)
    assert first.next_page_token == "page-2"

    # The user passes the token back to fetch the next page.
    last = ctx.stock_data.get_stock_bars(
        _bars_request(page_token=first.next_page_token),
        handle_pagination=PaginationType.NONE,
    )
    assert isinstance(last, BarSet)
    assert last.next_page_token is None
    return {"first": first, "last": last}
