"""Broker event streams.

The streams do not end, and reading the body in record mode would block, so
these scenarios serve one SSE event each. The request (path, query, Accept)
is still the one the SDK builds. ``get_all_accounts_positions`` is here too:
the live call returns every account's positions, which must not be committed.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from alpaca.broker.requests import GetEventsRequest
from alpaca.trading.models import AllAccountsPositions

from . import Context, scenario

BROKER = "broker"
EVENT = 'id: evt-1\ndata: {"status": "ACTIVE"}\n\n'
SSE = {"status": 200, "text": EVENT}
POSITIONS = {
    "as_of": "2024-03-04T21:00:00+00:00",
    "positions": {
        "00000000-0000-0000-0000-000000000001": [
            {
                "asset_id": "00000000-0000-0000-0000-000000000002",
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "asset_class": "us_equity",
                "avg_entry_price": "1",
                "qty": "1",
                "side": "long",
                "cost_basis": "1",
            }
        ]
    },
}


@scenario(
    covers=[
        "BrokerClient.get_account_status_events",
        "BrokerClient.get_trade_events",
        "BrokerClient.get_journal_events",
        "BrokerClient.get_transfer_events",
        "BrokerClient.get_non_trading_activity_events",
    ],
    credentials=BROKER,
    stub_responses=[SSE, SSE, SSE, SSE, SSE],
)
def event_stream_requests(ctx: Context) -> Dict[str, Any]:
    window = GetEventsRequest(since=date(2024, 3, 1), until=date(2024, 3, 8))
    streams = [
        ctx.broker.get_account_status_events(window),
        ctx.broker.get_trade_events(window),
        ctx.broker.get_journal_events(window),
        ctx.broker.get_transfer_events(window),
        ctx.broker.get_non_trading_activity_events(window),
    ]
    # The client yields the SSE ``data`` field, already a string.
    events = [next(stream) for stream in streams]
    assert events == ['{"status": "ACTIVE"}'] * 5
    return {"events": events}


@scenario(
    covers=["BrokerClient.get_all_accounts_positions"],
    credentials=BROKER,
    stub_responses=[{"status": 200, "json": POSITIONS}],
)
def bulk_positions_are_not_fetched_live(ctx: Context) -> Dict[str, Any]:
    # Deprecated, and the response is every account. One stubbed page freezes
    # the request the SDK sends without recording anyone else's positions.
    positions = ctx.broker.get_all_accounts_positions(page=1)
    assert isinstance(positions, AllAccountsPositions)
    assert len(positions.positions) == 1
    return {"positions": positions}
