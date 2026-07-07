from datetime import date, datetime, timezone
from typing import List

import pytest

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import Market, Phase
from alpaca.trading.models import (
    Clock,
    ClockResp,
    LegacyCalendarDay,
    PublicCalendarResp,
)
from alpaca.trading.requests import GetV3CalendarRequest, GetV3ClockRequest


@pytest.mark.parametrize("method_name", ["get_clock", "get_v2_clock"])
def test_get_v2_clock(reqmock, trading_client: TradingClient, method_name):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/clock",
        text="""
        {
          "timestamp": "2022-05-16T16:32:24.14373588-04:00",
          "is_open": false,
          "next_open": "2022-05-17T09:30:00-04:00",
          "next_close": "2022-05-17T16:00:00-04:00"
        }
        """,
    )

    result = getattr(trading_client, method_name)()

    assert reqmock.called_once
    assert isinstance(result, Clock)


@pytest.mark.parametrize("method_name", ["get_calendar", "get_v2_calendar"])
def test_get_v2_calendar_preserves_legacy_session_fields(
    reqmock, trading_client: TradingClient, method_name
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/calendar",
        text="""
        [
          {
            "date": "2025-01-02",
            "open": "09:30",
            "close": "16:00",
            "session_open": "0400",
            "session_close": "2000",
            "settlement_date": "2025-01-03"
          }
        ]
        """,
    )

    result = getattr(trading_client, method_name)()

    assert reqmock.called_once
    assert isinstance(result, List)
    assert len(result) == 1
    assert isinstance(result[0], LegacyCalendarDay)
    assert result[0].date == date(2025, 1, 2)
    assert result[0].open == "09:30"
    assert result[0].close == "16:00"
    assert result[0].session_open == "0400"
    assert result[0].session_close == "2000"
    assert result[0].settlement_date == date(2025, 1, 3)


def test_get_v3_calendar(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v3/calendar/NYSE",
        text="""
        {
          "market": {
            "acronym": "NYSE",
            "name": "New York Stock Exchange",
            "timezone": "America/New_York",
            "mic": "XNYS"
          },
          "calendar": [
            {
              "date": "2025-01-02",
              "core_start": "2025-01-02T09:30:00-05:00",
              "core_end": "2025-01-02T16:00:00-05:00",
              "pre_start": "2025-01-02T04:00:00-05:00",
              "pre_end": "2025-01-02T09:30:00-05:00",
              "post_start": "2025-01-02T16:00:00-05:00",
              "post_end": "2025-01-02T20:00:00-05:00",
              "settlement_date": "2025-01-03"
            }
          ]
        }
        """,
    )

    result = trading_client.get_v3_calendar(
        Market.NYSE,
        GetV3CalendarRequest(
            start=date(2025, 1, 2),
            end=date(2025, 1, 3),
            timezone="UTC",
        ),
    )

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {
        "start": ["2025-01-02"],
        "end": ["2025-01-03"],
        "timezone": ["utc"],
    }
    assert isinstance(result, PublicCalendarResp)
    assert result.market.acronym == "NYSE"
    assert len(result.calendar) == 1
    assert result.calendar[0].date == date(2025, 1, 2)
    assert result.calendar[0].settlement_date == date(2025, 1, 3)


def test_get_v3_calendar_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v3/calendar/NYSE",
        json={
            "market": {
                "acronym": "NYSE",
                "name": "New York Stock Exchange",
                "timezone": "America/New_York",
                "mic": "XNYS",
            },
            "calendar": [],
        },
    )

    result = trading_client_raw.get_v3_calendar("NYSE")

    assert reqmock.called_once
    assert result["market"]["acronym"] == "NYSE"
    assert result["calendar"] == []


def test_get_v3_clock(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v3/clock",
        text="""
        {
          "clocks": [
            {
              "market": {
                "acronym": "NYSE",
                "name": "New York Stock Exchange",
                "timezone": "America/New_York",
                "mic": "XNYS"
              },
              "timestamp": "2025-01-02T14:30:00Z",
              "is_market_day": true,
              "next_market_open": "2025-01-02T09:30:00-05:00",
              "next_market_close": "2025-01-02T16:00:00-05:00",
              "phase": "core",
              "phase_until": "2025-01-02T16:00:00-05:00"
            }
          ]
        }
        """,
    )

    result = trading_client.get_v3_clock(
        GetV3ClockRequest(
            markets=[Market.NYSE, "LSE"],
            time=datetime(2025, 1, 2, 14, 30, tzinfo=timezone.utc),
        )
    )

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {
        "markets": ["nyse,lse"],
        "time": ["2025-01-02t14:30:00+00:00"],
    }
    assert isinstance(result, ClockResp)
    assert len(result.clocks) == 1
    assert result.clocks[0].market.acronym == "NYSE"
    assert result.clocks[0].phase == Phase.CORE


def test_get_v3_clock_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v3/clock",
        json={"clocks": []},
    )

    result = trading_client_raw.get_v3_clock()

    assert reqmock.called_once
    assert result == {"clocks": []}
