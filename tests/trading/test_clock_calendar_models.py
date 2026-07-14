from alpaca.trading.enums import Market, Phase
from alpaca.trading.models import (
    CalendarDay,
    ClockResp,
    LegacyCalendarDay,
    LegacyClock,
    MarketClock,
    PublicCalendarResp,
    PublicMarket,
)
from alpaca.trading.requests import GetCalendarRequest


def test_clock_calendar_enums_match_api_values() -> None:
    assert [market.value for market in Market] == [
        "BMO",
        "BNYM",
        "BOATS",
        "CEUX",
        "CHIX",
        "HKEX",
        "IEX",
        "IEXG",
        "ISE",
        "LSE",
        "MTA",
        "MTAA",
        "NASDAQ",
        "NYSE",
        "OCEA",
        "OPRA",
        "OTC",
        "OTCM",
        "SIFMA",
        "TADAWUL",
        "XAMS",
        "XBRU",
        "XDUB",
        "XETR",
        "XETRA",
        "XHKG",
        "XLIS",
        "XLON",
        "XNAS",
        "XNYS",
        "XPAR",
        "XSAU",
    ]
    assert [phase.value for phase in Phase] == [
        "closed",
        "pre",
        "core",
        "lunch",
        "post",
    ]


def test_calendar_schemas_parse_legacy_and_public_responses() -> None:
    legacy = LegacyCalendarDay(
        date="2026-07-14",
        open="09:30",
        close="16:00",
        session_open="0700",
        session_close="1900",
        settlement_date="2026-07-15",
    )
    public = PublicCalendarResp(
        market={
            "acronym": "NYSE",
            "name": "New York Stock Exchange",
            "timezone": "America/New_York",
            "mic": "XNYS",
        },
        calendar=[
            {
                "date": "2026-07-14",
                "core_start": "2026-07-14T09:30:00-04:00",
                "core_end": "2026-07-14T16:00:00-04:00",
            }
        ],
    )

    assert legacy.date.isoformat() == "2026-07-14"
    assert legacy.settlement_date.isoformat() == "2026-07-15"
    assert public.market.mic == "XNYS"
    assert public.market.bic is None
    assert public.calendar[0].settlement_date is None


def test_clock_schemas_parse_legacy_and_public_responses() -> None:
    timestamp = "2026-07-14T12:00:00-04:00"
    next_open = "2026-07-15T09:30:00-04:00"
    next_close = "2026-07-14T16:00:00-04:00"
    legacy = LegacyClock(
        timestamp=timestamp,
        is_open=True,
        next_open=next_open,
        next_close=next_close,
    )
    response = ClockResp(
        clocks=[
            {
                "market": {
                    "acronym": "NYSE",
                    "name": "New York Stock Exchange",
                    "timezone": "America/New_York",
                },
                "timestamp": timestamp,
                "is_market_day": True,
                "next_market_open": next_open,
                "next_market_close": next_close,
                "phase": "core",
                "phase_until": next_close,
            }
        ]
    )

    assert legacy.is_open is True
    assert isinstance(response.clocks[0], MarketClock)
    assert isinstance(response.clocks[0].market, PublicMarket)
    assert response.clocks[0].phase == Phase.CORE


def test_calendar_day_optional_sessions_default_to_none() -> None:
    day = CalendarDay(
        date="2026-07-14",
        core_start="2026-07-14T09:30:00-04:00",
        core_end="2026-07-14T16:00:00-04:00",
    )

    assert day.pre_start is None
    assert day.pre_end is None
    assert day.lunch_start is None
    assert day.lunch_end is None
    assert day.post_start is None
    assert day.post_end is None


def test_get_calendar_request_defaults_to_trading_dates() -> None:
    request = GetCalendarRequest()

    assert request.date_type == "TRADING"
    assert request.to_request_fields() == {"date_type": "TRADING"}
