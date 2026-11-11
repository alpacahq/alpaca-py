"""Error responses the API returns on demand, and what users get from the SDK.

Users catch ``APIError`` and branch on ``status_code``, and often read
``code`` and ``message``. Each scenario snapshots the exception type and
those attributes, including when reading one of them raises.

Nothing here leaves anything on the paper account: every request is one the
API rejects. If an order is accepted anyway, it is canceled and the scenario
fails.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from alpaca.common.exceptions import APIError
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order
from alpaca.trading.requests import LimitOrderRequest

from . import Context, scenario
from ._errors import error_details

# A UUID no order will ever have, and a client order id nobody uses.
MISSING_ORDER_ID = UUID("00000000-0000-4000-8000-000000000000")
MISSING_CLIENT_ORDER_ID = "consumer-check-order-that-does-not-exist"


@scenario(covers=["TradingClient.get_account"])
def invalid_keys_raise_api_error(ctx: Context) -> Dict[str, Any]:
    try:
        ctx.trading_with_invalid_keys.get_account()
    except APIError as error:
        assert error.status_code in (401, 403)
        return error_details(error)
    raise AssertionError("invalid keys should be rejected")


@scenario(
    covers=["TradingClient.get_order_by_id", "TradingClient.get_order_by_client_id"]
)
def unknown_order_raises_not_found(ctx: Context) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        ctx.trading.get_order_by_id(MISSING_ORDER_ID)
    except APIError as error:
        assert error.status_code == 404
        results["by_id"] = error_details(error)
    else:
        raise AssertionError("an unknown order id should raise APIError")
    try:
        ctx.trading.get_order_by_client_id(MISSING_CLIENT_ORDER_ID)
    except APIError as error:
        assert error.status_code == 404
        results["by_client_id"] = error_details(error)
    else:
        raise AssertionError("an unknown client order id should raise APIError")
    return results


@scenario(covers=["TradingClient.submit_order"])
def rejected_orders_raise_api_error(ctx: Context) -> Dict[str, Any]:
    rejected = {
        # About $10M against a paper account's default $100k.
        "insufficient_buying_power": LimitOrderRequest(
            symbol="AAPL",
            qty=10_000_000,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=1.00,
            client_order_id=ctx.unique_id("too-big"),
        ),
        # Prices of $1 or more allow at most two decimals.
        "sub_penny_limit_price": LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=1.0001,
            client_order_id=ctx.unique_id("sub-penny"),
        ),
    }
    results: Dict[str, Any] = {}
    for label, request in rejected.items():
        try:
            order = ctx.trading.submit_order(request)
        except APIError as error:
            assert error.status_code is not None and 400 <= error.status_code < 500
            results[label] = error_details(error)
            continue
        if isinstance(order, Order):
            ctx.trading.cancel_order_by_id(order.id)
        raise AssertionError(f"{label}: the API accepted an order it should reject")
    return results


@scenario(covers=["CryptoHistoricalDataClient.get_crypto_bars"])
def end_before_start_raises_api_error(ctx: Context) -> Dict[str, Any]:
    # The data API answers 400 with {"message": ...} and no "code".
    try:
        ctx.crypto_data.get_crypto_bars(
            CryptoBarsRequest(
                symbol_or_symbols="BTC/USD",
                timeframe=TimeFrame.Hour,
                start=datetime(2024, 3, 5, tzinfo=timezone.utc),
                end=datetime(2024, 3, 4, tzinfo=timezone.utc),
            )
        )
    except APIError as error:
        assert error.status_code == 400
        return error_details(error)
    raise AssertionError("end before start should raise APIError")
