"""Locates, activities, watchlists by name, and the v3 clock and calendar.

Added in 0.50.0. Locates and the activities stream are not available on the
paper account these checks use, and a by-name watchlist write would change
that account, so every success path here is stubbed. Recorded with this
checkout's SDK until BASELINE reaches 0.50.0.

New SDK imports stay inside the scenarios so BASELINE can collect this module.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict

from . import Context, scenario

SINCE = "0.50.0"
EMPTY = {"status": 204, "text": ""}
CREATED_AT = "2026-01-02T15:04:05Z"
LOCATE_ID = "550e8400-e29b-41d4-a716-446655440000"
ORDER_ID = "b5abe576-6a8a-49f3-a353-46b72c1ccae9"
FILL_ID = "20220202135509981::2d7be4ff-d1f3-43e9-856a-0f5cf5c5088e"
DIVIDEND_ID = "20190801011955195::5f596936-6f23-4cef-bdf1-3806aae57dbf"
SINCE_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
UNTIL_AT = datetime(2026, 1, 2, tzinfo=timezone.utc)
MARKET = {
    "acronym": "NYSE",
    "name": "New York Stock Exchange",
    "timezone": "America/New_York",
    "bic": "IRVTUS3NXXX",
    "mic": "XNYS",
}
LOCATE = {
    "id": LOCATE_ID,
    "symbol": "TSLA",
    "requested_qty": 100,
    "located_qty": 100,
    "all_or_none": False,
    "status": "active",
    "created_at": CREATED_AT,
    "expires_at": "2026-01-03T01:00:00Z",
    "limit_price": "0.05",
    "located_price": "0.05",
    "total_fee": "5.00",
    "rejection_reason": "inventory_unavailable",
}
LOCATES_PAGE = {"locates": [LOCATE], "next_page_token": "next-page"}
LOCATE_QUOTES = {
    "quotes": [
        {
            "symbol": "TSLA",
            "available_qty": 1000,
            "price": "0.0123",
            "quoted_at": CREATED_AT,
        }
    ],
    "errors": [
        {"symbol": "FB", "code": "symbol_not_found", "message": "symbol not found"}
    ],
}
FILL = {
    "activity_type": "FILL",
    "cum_qty": "2",
    "id": FILL_ID,
    "leaves_qty": "0",
    "order_id": ORDER_ID,
    "order_status": "filled",
    "price": "174.78",
    "qty": "2",
    "side": "buy",
    "symbol": "AAPL",
    "transaction_time": "2022-02-02T18:55:09.981482Z",
    "type": "fill",
}
DIVIDEND = {
    "activity_sub_type": "SDIV",
    "activity_type": "DIV",
    "created_at": "2021-05-10T14:01:04.650275Z",
    "currency": "USD",
    "cusip": "90130A101",
    "date": "2019-08-01",
    "group_id": "group-1",
    "id": DIVIDEND_ID,
    "net_amount": "1.02",
    "per_share_amount": "0.51",
    "qty": "2",
    "status": "executed",
    "symbol": "T",
}
ACTIVITIES = [FILL, DIVIDEND]
CLOCK = {
    "clocks": [
        {
            "is_market_day": True,
            "timestamp": "2026-01-01T00:00:00Z",
            "next_market_open": "2026-01-02T14:30:00Z",
            "next_market_close": "2026-01-02T21:00:00Z",
            "phase": "closed",
            "phase_until": "2026-01-02T14:30:00Z",
            "market": MARKET,
        }
    ]
}
CALENDAR_DAY = {
    "date": "2026-07-01",
    "core_start": "2026-07-01T09:30:00-04:00",
    "core_end": "2026-07-01T16:00:00-04:00",
    "pre_start": "2026-07-01T04:00:00-04:00",
    "pre_end": "2026-07-01T09:30:00-04:00",
    "lunch_start": "2026-07-01T12:00:00-04:00",
    "lunch_end": "2026-07-01T13:00:00-04:00",
    "post_start": "2026-07-01T16:00:00-04:00",
    "post_end": "2026-07-01T20:00:00-04:00",
    "settlement_date": "2026-07-02",
}
CALENDAR = {
    "market": {
        **MARKET,
        "acronym": "BMO",
        "name": "BMO",
        "timezone": "America/Toronto",
    },
    "calendar": [CALENDAR_DAY],
}
WATCHLIST = {
    "id": "00000000-0000-4000-8000-000000000002",
    "account_id": "00000000-0000-4000-8000-000000000001",
    "name": "Tech",
    "created_at": CREATED_AT,
    "updated_at": CREATED_AT,
}
SSE_BODY = 'data: {"activity_type":"FILL","qty":"1"}\n\n'


def _json(body: Any) -> Dict[str, Any]:
    return {"status": 200, "json": body}


@scenario(
    covers=[
        "TradingClient.get_locates",
        "TradingClient.create_locate",
        "TradingClient.get_locate",
        "TradingClient.get_locate_quotes",
    ],
    since=SINCE,
    stub_responses=[
        _json(LOCATES_PAGE),
        _json(LOCATE),
        _json(LOCATE),
        _json(LOCATE_QUOTES),
    ],
)
def locates_and_quotes(ctx: Context) -> Dict[str, Any]:
    from datetime import date as date_cls

    from alpaca.trading.enums import LocateQuoteErrorCode, LocateStatus
    from alpaca.trading.models import (
        ListLocateQuotesResponse,
        ListLocatesResponse,
        Locate,
    )
    from alpaca.trading.requests import (
        CreateLocateRequest,
        GetLocateQuotesRequest,
        GetLocatesRequest,
    )

    page = ctx.trading.get_locates(
        GetLocatesRequest(
            symbol="TSLA",
            status=LocateStatus.ACTIVE,
            limit=1000,
            start=date_cls(2026, 1, 1),
            end=date_cls(2026, 1, 31),
            page_token="next-page",
        )
    )
    created = ctx.trading.create_locate(
        CreateLocateRequest(
            symbol="TSLA", qty=100, all_or_none=False, limit_price="0.05"
        )
    )
    fetched = ctx.trading.get_locate(LOCATE_ID)
    quotes = ctx.trading.get_locate_quotes(
        GetLocateQuotesRequest(symbols=["TSLA", "AAPL"])
    )

    assert isinstance(page, ListLocatesResponse)
    assert page.next_page_token == "next-page"
    assert isinstance(page.locates[0], Locate)
    assert page.locates[0].status == LocateStatus.ACTIVE
    assert page.locates[0].requested_qty == 100
    assert isinstance(created, Locate)
    assert isinstance(fetched, Locate)
    assert str(fetched.id) == LOCATE_ID
    assert isinstance(quotes, ListLocateQuotesResponse)
    assert quotes.quotes[0].symbol == "TSLA"
    assert quotes.quotes[0].available_qty == 1000
    assert quotes.errors is not None
    assert quotes.errors[0].code == LocateQuoteErrorCode.SYMBOL_NOT_FOUND
    return {"page": page, "created": created, "fetched": fetched, "quotes": quotes}


@scenario(
    covers=[
        "TradingClient.get_account_activities",
        "TradingClient.get_account_activities_by_type",
        "TradingClient.subscribe_to_activities_sse",
    ],
    since=SINCE,
    stub_responses=[
        _json(ACTIVITIES),
        _json([FILL]),
        _json([FILL]),
        _json([DIVIDEND]),
        {
            "status": 200,
            "text": SSE_BODY,
            "headers": {"Content-Type": "text/event-stream"},
        },
    ],
)
def account_activities_and_stream(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.enums import (
        GetAccountActivitiesCategoryParameter,
        GetAccountActivitiesDirectionParameter,
    )
    from alpaca.trading.models import NonTradeActivities, TradingActivities
    from alpaca.trading.requests import (
        ActivityEventsRequest,
        GetAccountActivitiesByTypeRequest,
        GetAccountActivitiesRequest,
    )

    ranged = ctx.trading.get_account_activities(
        GetAccountActivitiesRequest(
            activity_types=["FILL", "DIV"],
            order_id=ORDER_ID,
            after=SINCE_AT,
            until=UNTIL_AT,
            direction=GetAccountActivitiesDirectionParameter.DESC,
            page_size=100,
            page_token=FILL_ID,
        )
    )
    # ``date`` cannot be combined with ``after`` or ``until``, and ``category``
    # cannot be combined with ``activity_types``.
    for_day = ctx.trading.get_account_activities(
        GetAccountActivitiesRequest(
            category=GetAccountActivitiesCategoryParameter.TRADE_ACTIVITY,
            date=datetime(2022, 2, 2, tzinfo=timezone.utc),
        )
    )
    fills = ctx.trading.get_account_activities_by_type(
        "FILL",
        GetAccountActivitiesByTypeRequest(
            order_id=ORDER_ID,
            after=SINCE_AT,
            until=UNTIL_AT,
            direction=GetAccountActivitiesDirectionParameter.DESC,
            page_size=100,
            page_token=FILL_ID,
        ),
    )
    dividends = ctx.trading.get_account_activities_by_type(
        "DIV",
        GetAccountActivitiesByTypeRequest(
            date=datetime(2019, 8, 1, tzinfo=timezone.utc)
        ),
    )
    events = list(
        ctx.trading.subscribe_to_activities_sse(
            ActivityEventsRequest(
                since=SINCE_AT,
                until=UNTIL_AT,
                since_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
                until_id="01ARZ3NDEKTSV4RRFFQ69G5FB0",
            )
        )
    )

    assert isinstance(ranged, list) and isinstance(ranged[0], TradingActivities)
    assert ranged[0].price == "174.78"
    assert isinstance(ranged[1], NonTradeActivities)
    assert ranged[1].net_amount == "1.02"
    assert isinstance(for_day, list) and isinstance(for_day[0], TradingActivities)
    assert isinstance(fills, list) and isinstance(fills[0], TradingActivities)
    assert isinstance(dividends, list) and isinstance(dividends[0], NonTradeActivities)
    assert dividends[0].symbol == "T"
    assert events == ['{"activity_type":"FILL","qty":"1"}']
    return {
        "ranged": ranged,
        "for_day": for_day,
        "fills": fills,
        "dividends": dividends,
        "events": events,
    }


@scenario(
    covers=[
        "TradingClient.get_watchlist_by_name",
        "TradingClient.add_asset_to_watchlist_by_name",
        "TradingClient.update_watchlist_by_name",
        "TradingClient.delete_watchlist_by_name",
    ],
    since=SINCE,
    stub_responses=[_json(WATCHLIST), _json(WATCHLIST), _json(WATCHLIST), EMPTY],
)
def watchlists_by_name(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.models import Watchlist
    from alpaca.trading.requests import (
        AddAssetToWatchlistRequest,
        UpdateWatchlistRequest,
    )

    fetched = ctx.trading.get_watchlist_by_name("Tech")
    added = ctx.trading.add_asset_to_watchlist_by_name(
        "Tech", AddAssetToWatchlistRequest(symbol="AAPL")
    )
    updated = ctx.trading.update_watchlist_by_name(
        "Tech", UpdateWatchlistRequest(name="Tech", symbols=["AAPL"])
    )
    ctx.trading.delete_watchlist_by_name("Tech")

    assert isinstance(fetched, Watchlist)
    assert fetched.name == "Tech"
    assert isinstance(added, Watchlist)
    assert isinstance(updated, Watchlist)
    assert updated.name == "Tech"
    return {"fetched": fetched, "added": added, "updated": updated}


@scenario(
    covers=["TradingClient.get_v3_clock", "TradingClient.get_v3_calendar"],
    since=SINCE,
    stub_responses=[_json(CLOCK), _json(CALENDAR)],
)
def v3_clock_and_calendar(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.enums import CalendarTimezoneParameter, Phase
    from alpaca.trading.models import ClockResp, PublicCalendarResp
    from alpaca.trading.requests import GetV3CalendarRequest, GetV3ClockRequest

    clock = ctx.trading.get_v3_clock(
        GetV3ClockRequest(markets="NYSE,LSE", time=SINCE_AT)
    )
    calendar = ctx.trading.get_v3_calendar(
        "BMO",
        GetV3CalendarRequest(
            start=date(2026, 7, 1),
            end=date(2026, 7, 31),
            timezone=CalendarTimezoneParameter.UTC,
        ),
    )

    assert isinstance(clock, ClockResp)
    assert clock.clocks[0].phase == Phase.CLOSED
    assert clock.clocks[0].market.acronym == "NYSE"
    assert clock.clocks[0].market.mic == "XNYS"
    assert isinstance(calendar, PublicCalendarResp)
    assert calendar.market.acronym == "BMO"
    day = calendar.calendar[0]
    assert day.var_date == date(2026, 7, 1)
    assert day.settlement_date == date(2026, 7, 2)
    return {"clock": clock, "calendar": calendar}
