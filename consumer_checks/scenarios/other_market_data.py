"""Fixed-income, logo and corporate-action stream contracts added in 0.50.0.

The consumer account lacks fixed-income and logo subscriptions. Fixed responses
exercise their success paths without entitled keys. Fixed-income payloads come
from the pinned Market Data spec's examples. The SSE fixture ends after two
events so the recorder can buffer it without waiting on a live stream.
These scenarios use stub responses in every mode, including live mode.

New SDK imports stay inside the scenarios so BASELINE can collect this module.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict

from . import Context, scenario

SINCE = "0.50.0"
PRICE_ISIN = "US912797KJ59"
QUOTE_ISIN = "US912797SX61"
PRICES = {
    "prices": {
        PRICE_ISIN: {
            "p": 99.6459,
            "t": "2025-02-14T20:58:00.648Z",
            "ytm": 4.249,
            "ytw": 4.249,
        }
    }
}
QUOTES = {
    "quotes": {
        QUOTE_ISIN: {
            "ams": 1000,
            "ap": 99.91958333,
            "as": 1000000,
            "aytm": 2.226923,
            "aytw": 2.226923,
            "bms": 1000,
            "bp": 99.81091667,
            "bs": 1000000,
            "bytm": 5.236154,
            "bytw": 5.236154,
            "t": "2026-05-21T06:56:01.882466873Z",
        }
    }
}
# A one-pixel PNG with non-UTF-8 bytes, to exercise binary recording and replay.
PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
EVENT_ID = "01J9RPMV5TKB8WX3M4F1KZ7QH2"
UNTIL_ID = "01J9RVB6Y4ZK8M3N7QD2WX1RFP"
EVENT = {
    "action": "insert",
    "event_id": EVENT_ID,
    "event_type": "cash_dividend_corporateaction_event",
    "region": "us",
    "at": "2026-03-20T12:24:58.807230Z",
    "ca": {
        "id": "1dbc7685-9517-4a77-a236-8527d49cefdc",
        "symbol": "AAPL",
        "cusip": "037833100",
        "currency": "USD",
        "ex_date": "2026-05-09",
        "payable_date": "2026-05-15",
        "process_date": "2026-05-15",
        "record_date": "2026-05-12",
        "rate": "0.24",
        "foreign": False,
        "special": False,
    },
}
UPDATED_EVENT = {**EVENT, "action": "update", "event_id": UNTIL_ID}
SSE_BODY = (
    ": heartbeat\n\n"
    f"id: {EVENT_ID}\ndata: {json.dumps(EVENT)}\n\n"
    f"id: {UNTIL_ID}\ndata: {json.dumps(UPDATED_EVENT)}\n\n"
)


@scenario(
    covers=["FixedIncomeClient.get_fixed_income_latest_prices"],
    since=SINCE,
    stub_responses=[{"status": 200, "json": PRICES}],
)
def fixed_income_latest_prices(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import FixedIncomeLatestPricesResp
    from alpaca.data.requests import FixedIncomeLatestPricesRequest

    result = ctx.fixed_income.get_fixed_income_latest_prices(
        FixedIncomeLatestPricesRequest(isins=[PRICE_ISIN, QUOTE_ISIN])
    )
    assert isinstance(result, FixedIncomeLatestPricesResp)
    price = result.prices[PRICE_ISIN]
    assert price.p == 99.6459
    assert price.ytm == price.ytw == 4.249
    assert isinstance(price.t, datetime)
    return {"prices": result}


@scenario(
    covers=["FixedIncomeClient.get_fixed_income_latest_quotes"],
    since=SINCE,
    stub_responses=[{"status": 200, "json": QUOTES}],
)
def fixed_income_latest_quotes(ctx: Context) -> Dict[str, Any]:
    from alpaca.data import FixedIncomeLatestQuotesResp
    from alpaca.data.requests import FixedIncomeLatestQuotesRequest

    result = ctx.fixed_income.get_fixed_income_latest_quotes(
        FixedIncomeLatestQuotesRequest(isins=QUOTE_ISIN, trade_size=1000)
    )
    assert isinstance(result, FixedIncomeLatestQuotesResp)
    quote = result.quotes[QUOTE_ISIN]
    assert quote.bp == 99.81091667 and quote.ap == 99.91958333
    assert quote.bs == quote.var_as == 1000000
    assert quote.bms == quote.ams == 1000
    assert isinstance(quote.t, datetime)
    return {"quotes": result}


@scenario(
    covers=["LogoClient.get_logo"],
    since=SINCE,
    stub_responses=[
        {
            "status": 200,
            "base64": PNG_BASE64,
            "headers": {"Content-Type": "image/png"},
        }
    ]
    * 3,
)
def logo_png_and_placeholder(ctx: Context) -> Dict[str, Any]:
    default = ctx.logos.get_logo("AAPL")
    without_placeholder = ctx.logos.get_logo("MSFT", placeholder=False)
    with_placeholder = ctx.logos.get_logo("UNKNOWN", placeholder=True)

    assert isinstance(default, bytes)
    assert default.startswith(b"\x89PNG\r\n\x1a\n")
    assert (
        default
        == without_placeholder
        == with_placeholder
        == base64.b64decode(PNG_BASE64)
    )
    return {
        "default": default,
        "without_placeholder": without_placeholder,
        "with_placeholder": with_placeholder,
    }


@scenario(
    covers=["CorporateActionsClient.get_corporate_action_events"],
    since=SINCE,
    stub_responses=[
        {
            "status": 200,
            "text": SSE_BODY,
            "headers": {"Content-Type": "text/event-stream"},
        }
    ],
)
def corporate_action_events_with_filters_and_reconnect(ctx: Context) -> Dict[str, Any]:
    from alpaca.data.requests import CorporateActionEventsRequest

    request = CorporateActionEventsRequest(
        type=[
            "cash_dividend_corporateaction_event",
            "stock_dividend_corporateaction_event",
        ],
        region="us",
        since=datetime(2026, 3, 20, tzinfo=timezone.utc),
        until=datetime(2026, 3, 21, tzinfo=timezone.utc),
        since_id=EVENT_ID,
        until_id=UNTIL_ID,
        last_event_id=EVENT_ID,
    )
    events = list(ctx.corporate_actions.get_corporate_action_events(request))

    assert len(events) == 2
    assert all(isinstance(event, str) for event in events)
    assert [json.loads(event) for event in events] == [EVENT, UPDATED_EVENT]
    return {"events": events}
