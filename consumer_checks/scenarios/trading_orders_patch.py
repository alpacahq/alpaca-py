"""Replacing an order with ``PatchOrderRequest``, ``since="0.46.0"``.

``PatchOrderRequest`` is the generated request that replaces ``ReplaceOrderRequest``.
These scenarios send it with every field set, so what the SDK puts on the wire
(string numbers, ``time_in_force``, the nested ``advanced_instructions``) is
frozen. The paper API accepts only some combinations (``notional`` is for IPO
indications of interest, ``advanced_instructions`` needs Elite Smart Router), so
the responses are stubbed, like ``errors_stubbed``. Recorded with this
checkout's SDK until BASELINE reaches 0.46.0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from alpaca.trading.enums import (
    AdvancedInstructionsAlgorithm,
    AdvancedInstructionsDestination,
    OrderStatus,
    TimeInForce,
)
from alpaca.trading.models import Order
from alpaca.trading.requests import AdvancedInstructions, PatchOrderRequest

from . import Context, scenario

SINCE = "0.46.0"
ORIGINAL_ID = UUID("0b1f8e2c-5a3d-4c6e-9f10-2d7a8b9c0e11")
REPLACEMENT_ID = "6c2d4f8a-1b3e-4a5c-8d7f-9e0a1b2c3d4e"


def _order(**overrides: Any) -> Dict[str, Any]:
    """The JSON the API returns for a replacement order."""
    order = {
        "id": REPLACEMENT_ID,
        "client_order_id": "patched",
        "created_at": "2024-03-04T15:00:00.000000Z",
        "updated_at": "2024-03-04T15:00:00.000000Z",
        "submitted_at": "2024-03-04T15:00:00.000000Z",
        "expired_at": None,
        "filled_at": None,
        "canceled_at": None,
        "failed_at": None,
        "replaced_at": None,
        "replaced_by": None,
        "replaces": str(ORIGINAL_ID),
        "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
        "symbol": "AAPL",
        "asset_class": "us_equity",
        "notional": None,
        "qty": "4",
        "filled_qty": "0",
        "filled_avg_price": None,
        "order_class": "",
        "order_type": "limit",
        "type": "limit",
        "side": "buy",
        "time_in_force": "gtc",
        "limit_price": "1.01",
        "stop_price": None,
        "status": "new",
        "extended_hours": False,
        "legs": None,
        "trail_percent": None,
        "trail_price": None,
        "hwm": None,
        "position_intent": "buy_to_open",
    }
    order.update(overrides)
    return order


@scenario(
    covers=["TradingClient.replace_order_by_id"],
    since=SINCE,
    stub_responses=[
        {
            "status": 200,
            "json": _order(
                client_order_id="patched-limit",
                type="stop_limit",
                order_type="stop_limit",
                stop_price="1.5",
            ),
        }
    ],
)
def patch_order_shares_prices_and_routing(ctx: Context) -> Dict[str, Any]:
    patched = ctx.trading.replace_order_by_id(
        ORIGINAL_ID,
        PatchOrderRequest(
            qty="4",
            limit_price="1.01",
            stop_price="1.5",
            time_in_force=TimeInForce.GTC,
            client_order_id="patched-limit",
            advanced_instructions=AdvancedInstructions(
                algorithm=AdvancedInstructionsAlgorithm.VWAP,
                destination=AdvancedInstructionsDestination.NASDAQ,
                display_qty="100",
                max_percentage="0.314",
                start_time=datetime(2025, 7, 21, 13, 30, tzinfo=timezone.utc),
                end_time=datetime(2025, 7, 21, 19, 30, tzinfo=timezone.utc),
            ),
        ),
    )
    assert isinstance(patched, Order)
    assert patched.replaces == ORIGINAL_ID
    assert patched.status == OrderStatus.NEW
    assert patched.time_in_force == TimeInForce.GTC
    assert patched.stop_price == "1.5"
    return {"patched": patched}


@scenario(
    covers=["TradingClient.replace_order_by_id"],
    since=SINCE,
    stub_responses=[
        {
            "status": 200,
            "json": _order(
                client_order_id="patched-trail",
                type="trailing_stop",
                order_type="trailing_stop",
                limit_price=None,
                trail_price="0.5",
            ),
        }
    ],
)
def patch_trailing_stop_trail(ctx: Context) -> Dict[str, Any]:
    patched = ctx.trading.replace_order_by_id(
        ORIGINAL_ID,
        PatchOrderRequest(trail="0.5", client_order_id="patched-trail"),
    )
    assert isinstance(patched, Order)
    assert patched.trail_price == "0.5"
    return {"patched": patched}


@scenario(
    covers=["TradingClient.replace_order_by_id"],
    since=SINCE,
    stub_responses=[
        {
            "status": 200,
            "json": _order(
                client_order_id="patched-notional",
                asset_class="ipo",
                notional="750",
                qty=None,
            ),
        }
    ],
)
def patch_notional_amount(ctx: Context) -> Dict[str, Any]:
    patched = ctx.trading.replace_order_by_id(
        ORIGINAL_ID,
        PatchOrderRequest(notional="750", client_order_id="patched-notional"),
    )
    assert isinstance(patched, Order)
    assert patched.notional == "750"
    return {"patched": patched}
