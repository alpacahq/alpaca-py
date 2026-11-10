from urllib.parse import parse_qs, urlparse

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import ClockResp, PublicCalendarResp
from alpaca.trading.requests import GetV3CalendarRequest, GetV3ClockRequest

_PAPER = BaseURL.TRADING_PAPER.value
_CALENDAR = {
    "market": {
        "acronym": "BMO",
        "name": "BMO",
        "timezone": "America/Toronto",
    },
    "calendar": [
        {
            "date": "2026-07-01",
            "core_start": "2026-07-01T09:30:00-04:00",
            "core_end": "2026-07-01T16:00:00-04:00",
        }
    ],
}
_CLOCK = {
    "clocks": [
        {
            "is_market_day": True,
            "timestamp": "2026-01-01T00:00:00Z",
            "next_market_open": "2026-01-02T14:30:00Z",
            "next_market_close": "2026-01-02T21:00:00Z",
            "phase": "closed",
            "phase_until": "2026-01-02T14:30:00Z",
            "market": {
                "acronym": "NYSE",
                "name": "New York Stock Exchange",
                "timezone": "America/New_York",
            },
        }
    ]
}


def test_v3_clock_and_calendar_keep_v2_routes(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{_PAPER}/v2/clock",
        json={
            "timestamp": "2026-01-01T00:00:00Z",
            "is_open": False,
            "next_open": "2026-01-02T14:30:00Z",
            "next_close": "2026-01-02T21:00:00Z",
        },
    )
    reqmock.get(f"{_PAPER}/v3/clock", json=_CLOCK)
    reqmock.get(f"{_PAPER}/v3/calendar/BMO", json=_CALENDAR)

    trading_client.get_clock()
    clock = trading_client.get_v3_clock(
        GetV3ClockRequest(markets="NYSE,LSE", time="2026-01-01T00:00:00Z")
    )
    calendar = trading_client.get_v3_calendar(
        "BMO",
        GetV3CalendarRequest(start="2026-07-01", end="2026-07-31", timezone="UTC"),
    )

    assert urlparse(reqmock.request_history[0].url).path == "/v2/clock"
    clock_request = reqmock.request_history[1]
    clock_query = parse_qs(urlparse(clock_request.url).query)
    assert clock_request.method == "GET"
    assert urlparse(clock_request.url).path == "/v3/clock"
    assert clock_query["markets"] == ["NYSE,LSE"]
    assert "time" in clock_query
    assert isinstance(clock, ClockResp)
    assert clock.clocks[0].market.acronym == "NYSE"
    calendar_request = reqmock.request_history[2]
    assert urlparse(calendar_request.url).path == "/v3/calendar/BMO"
    calendar_query = parse_qs(urlparse(calendar_request.url).query)
    assert calendar_query["start"] == ["2026-07-01"]
    assert calendar_query["timezone"] == ["UTC"]
    assert isinstance(calendar, PublicCalendarResp)
    assert calendar.market.acronym == "BMO"


def test_get_v3_clock_honors_raw_data_and_url_override(reqmock):
    client = TradingClient(
        "key-id",
        "secret-key",
        raw_data=True,
        url_override="https://override.example",
    )
    reqmock.get("https://override.example/v3/clock", json=_CLOCK)

    clock = client.get_v3_clock()

    assert clock["clocks"][0]["phase"] == "closed"
    assert urlparse(reqmock.request_history[0].url).path == "/v3/clock"
