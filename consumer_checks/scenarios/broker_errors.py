"""Broker errors a user catches, plus raw JSON responses."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict
from uuid import UUID

from alpaca.common.exceptions import APIError
from alpaca.trading.requests import GetCalendarRequest

from . import Context, scenario
from ._errors import error_details

BROKER = "broker"
UNKNOWN_ACCOUNT = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")


@scenario(covers=["BrokerClient.get_clock"], credentials=BROKER)
def invalid_keys_raise_api_error(ctx: Context) -> Dict[str, Any]:
    try:
        ctx.broker_with_invalid_keys.get_clock()
    except APIError as error:
        assert error.status_code in (401, 403)
        return error_details(error)
    raise AssertionError("invalid broker keys should be rejected")


@scenario(
    covers=["BrokerClient.get_account_by_id", "BrokerClient.get_clock"],
    credentials=BROKER,
)
def unknown_account_raises_api_error(ctx: Context) -> Dict[str, Any]:
    # The broker API reports a missing account as 401, not 404, which is also
    # what rejected keys get. A call that must succeed first proves the keys
    # work, so a recording of bad keys cannot pass for a missing account.
    ctx.broker.get_clock()
    try:
        ctx.broker.get_account_by_id(UNKNOWN_ACCOUNT)
    except APIError as error:
        assert isinstance(error.status_code, int)
        assert 400 <= error.status_code < 500
        return error_details(error)
    raise AssertionError("an unknown account id should raise APIError")


@scenario(covers=["BrokerClient.get_asset"], credentials=BROKER)
def unknown_asset_raises_api_error(ctx: Context) -> Dict[str, Any]:
    try:
        ctx.broker.get_asset("NOT-A-REAL-SYMBOL")
    except APIError as error:
        assert isinstance(error.status_code, int)
        assert 400 <= error.status_code < 500
        # 401 and 403 mean the keys were rejected, not that the symbol is unknown.
        assert error.status_code not in (401, 403)
        return error_details(error)
    raise AssertionError("an unknown symbol should raise APIError")


@scenario(
    covers=[
        "BrokerClient.get_clock",
        "BrokerClient.get_calendar",
        "BrokerClient.get_asset",
    ],
    credentials=BROKER,
)
def broker_raw_responses(ctx: Context) -> Dict[str, Any]:
    clock = ctx.raw_broker.get_clock()
    asset = ctx.raw_broker.get_asset("AAPL")
    days = ctx.raw_broker.get_calendar(
        GetCalendarRequest(start=date(2024, 3, 4), end=date(2024, 3, 8))
    )

    assert isinstance(clock, dict) and isinstance(clock["is_open"], bool)
    assert isinstance(asset, dict) and asset["symbol"] == "AAPL"
    assert asset["class"] == "us_equity"
    assert isinstance(days, list) and len(days) == 5
    first = days[0]
    assert isinstance(first, dict)
    assert first["date"] == "2024-03-04"
    return {"clock": clock, "asset": asset, "days": days}
