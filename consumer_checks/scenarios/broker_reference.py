"""Broker API reference data. No account, and nothing is created."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from alpaca.trading.enums import AssetClass, AssetStatus, CorporateActionType
from alpaca.trading.models import Asset, Calendar, Clock, CorporateActionAnnouncement
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetCalendarRequest,
    GetCorporateAnnouncementsRequest,
)

from . import Context, scenario

BROKER = "broker"


@scenario(covers=["BrokerClient.get_clock"], credentials=BROKER)
def market_clock(ctx: Context) -> Dict[str, Any]:
    clock = ctx.broker.get_clock()

    assert isinstance(clock, Clock)
    assert isinstance(clock.is_open, bool)
    assert clock.next_close > clock.timestamp
    assert clock.timestamp.tzinfo is not None
    return {"clock": clock}


@scenario(covers=["BrokerClient.get_calendar"], credentials=BROKER)
def trading_calendar_for_a_week(ctx: Context) -> Dict[str, Any]:
    days = ctx.broker.get_calendar(
        GetCalendarRequest(start=date(2024, 3, 1), end=date(2024, 3, 8))
    )

    assert isinstance(days, list)
    assert [day.date for day in days] == [
        date(2024, 3, 1),
        date(2024, 3, 4),
        date(2024, 3, 5),
        date(2024, 3, 6),
        date(2024, 3, 7),
        date(2024, 3, 8),
    ]
    assert all(isinstance(day, Calendar) for day in days)
    assert days[0].open < days[0].close
    return {"days": days}


@scenario(
    covers=["BrokerClient.get_all_assets", "BrokerClient.get_asset"], credentials=BROKER
)
def active_crypto_assets(ctx: Context) -> Dict[str, Any]:
    # Filtered to crypto: the unfiltered list is about 10,000 assets.
    assets = ctx.broker.get_all_assets(
        GetAssetsRequest(asset_class=AssetClass.CRYPTO, status=AssetStatus.ACTIVE)
    )

    assert isinstance(assets, list)
    assert all(isinstance(asset, Asset) for asset in assets)
    assert all(asset.asset_class == AssetClass.CRYPTO for asset in assets)
    btc = [asset for asset in assets if asset.symbol == "BTC/USD"]
    assert len(btc) == 1

    by_symbol = ctx.broker.get_asset("AAPL")
    assert isinstance(by_symbol, Asset)
    assert by_symbol.symbol == "AAPL"
    assert by_symbol.asset_class == AssetClass.US_EQUITY
    # The full crypto list changes as assets are listed; the snapshot keeps one.
    return {"btc": btc[0], "aapl": by_symbol}


@scenario(
    covers=[
        "BrokerClient.get_corporate_announcements",
        "BrokerClient.get_corporate_announcement_by_id",
    ],
    credentials=BROKER,
)
def dividend_announcements(ctx: Context) -> Dict[str, Any]:
    # Both methods are deprecated. Users still call them, so removing them is a break.
    # AAPL declared a dividend on 1 February 2024. The range must be at most 90 days.
    announcements = ctx.broker.get_corporate_announcements(
        GetCorporateAnnouncementsRequest(
            ca_types=[CorporateActionType.DIVIDEND],
            since=date(2024, 1, 1),
            until=date(2024, 3, 1),
            symbol="AAPL",
        )
    )

    assert isinstance(announcements, list)
    assert announcements
    first = announcements[0]
    assert isinstance(first, CorporateActionAnnouncement)
    assert first.initiating_symbol == "AAPL"

    by_id = ctx.broker.get_corporate_announcement_by_id(first.id)
    assert isinstance(by_id, CorporateActionAnnouncement)
    assert by_id.id == first.id
    return {"announcements": announcements, "by_id": by_id}
