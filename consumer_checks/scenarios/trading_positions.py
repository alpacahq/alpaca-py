"""Trading API: replacing an order, and opening and closing a small position.

Both scenarios clean up after themselves, also when a check fails part way.
Account-wide methods (cancel_orders, close_all_positions,
set_account_configurations) are in trading_account_wide.py.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from alpaca.trading.enums import (
    AssetClass,
    OrderSide,
    OrderStatus,
    PositionSide,
    TimeInForce,
)
from alpaca.trading.models import Order, Position
from alpaca.trading.requests import (
    ClosePositionRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    ReplaceOrderRequest,
)

from . import Context, scenario

# Far below the market so the order never fills.
UNFILLABLE_LIMIT_PRICE = 1.00
# Crypto trades around the clock, so this scenario records at any hour.
CRYPTO_SYMBOL = "BTC/USD"
CRYPTO_POSITION_SYMBOL = "BTCUSD"  # positions use the symbol without the slash
CRYPTO_NOTIONAL = 10


def _cancel_best_effort(ctx: Context, order_id: UUID) -> None:
    """Failure-path cleanup: cancel the order, or the order that replaced it.

    Never raises, so the error that sent us here is the one reported.
    """
    try:
        order = ctx.trading.get_order_by_id(order_id)
        target = order_id
        if isinstance(order, Order) and order.replaced_by is not None:
            target = order.replaced_by
        ctx.trading.cancel_order_by_id(target)
    except Exception:  # already canceled or filled, or the SDK itself is broken
        pass


def _open_position_or_none(ctx: Context) -> Optional[Position]:
    try:
        position = ctx.trading.get_open_position(CRYPTO_POSITION_SYMBOL)
    except Exception:
        return None
    return position if isinstance(position, Position) else None


@scenario(covers=["TradingClient.replace_order_by_id"])
def replace_limit_order_price(ctx: Context) -> Dict[str, Any]:
    original = ctx.trading.submit_order(
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=UNFILLABLE_LIMIT_PRICE,
            client_order_id=ctx.unique_id("original"),
        )
    )
    assert isinstance(original, Order)
    replacement: Optional[Order] = None
    try:
        # An order still in pending_new cannot be replaced yet.
        current = original
        for _ in range(10):
            if current.status != OrderStatus.PENDING_NEW:
                break
            ctx.sleep(1)
            fetched = ctx.trading.get_order_by_id(original.id)
            assert isinstance(fetched, Order)
            current = fetched

        replaced = ctx.trading.replace_order_by_id(
            original.id,
            ReplaceOrderRequest(
                limit_price=UNFILLABLE_LIMIT_PRICE + 0.01,
                client_order_id=ctx.unique_id("replacement"),
            ),
        )
        assert isinstance(replaced, Order)
        replacement = replaced
        assert replacement.id != original.id
        assert replacement.replaces == original.id
        assert replacement.limit_price is not None
        assert Decimal(str(replacement.limit_price)) == Decimal("1.01")
    finally:
        if replacement is not None:
            ctx.trading.cancel_order_by_id(replacement.id)
        else:
            # The replace may have gone through even if the SDK then failed to
            # return it, in which case the open order is the replacement.
            _cancel_best_effort(ctx, original.id)

    old = ctx.trading.get_order_by_id(original.id)
    for _ in range(10):
        assert isinstance(old, Order)
        if old.status == OrderStatus.REPLACED:
            break
        ctx.sleep(1)
        old = ctx.trading.get_order_by_id(original.id)
    assert isinstance(old, Order)
    assert old.status == OrderStatus.REPLACED
    assert old.replaced_by == replacement.id
    return {"original": original, "replacement": replacement, "old_after": old}


def _wait_until_filled(ctx: Context, order: Order) -> Order:
    current = order
    for _ in range(15):
        if current.status == OrderStatus.FILLED:
            return current
        ctx.sleep(1)
        fetched = ctx.trading.get_order_by_id(order.id)
        assert isinstance(fetched, Order)
        current = fetched
    return current


@scenario(
    covers=[
        "TradingClient.get_all_positions",
        "TradingClient.get_open_position",
        "TradingClient.close_position",
    ]
)
def crypto_position_round_trip(ctx: Context) -> Dict[str, Any]:
    buy = ctx.trading.submit_order(
        MarketOrderRequest(
            symbol=CRYPTO_SYMBOL,
            notional=CRYPTO_NOTIONAL,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            client_order_id=ctx.unique_id("buy"),
        )
    )
    assert isinstance(buy, Order)
    bought = _wait_until_filled(ctx, buy)
    if bought.status != OrderStatus.FILLED:
        # It may fill between the last poll and the cancel: read it again.
        _cancel_best_effort(ctx, buy.id)
        latest = ctx.trading.get_order_by_id(buy.id)
        assert isinstance(latest, Order)
        if latest.status != OrderStatus.FILLED:
            raise AssertionError(f"market buy did not fill: {latest.status}")
        bought = latest
    assert bought.filled_qty is not None
    filled_qty = Decimal(str(bought.filled_qty))

    position: Optional[Position] = None
    closing: Any = None
    try:
        positions = ctx.trading.get_all_positions()
        assert isinstance(positions, list)
        listed = [p for p in positions if p.symbol == CRYPTO_POSITION_SYMBOL]
        assert len(listed) == 1

        fetched = ctx.trading.get_open_position(CRYPTO_POSITION_SYMBOL)
        assert isinstance(fetched, Position)
        position = fetched
        assert position.asset_class == AssetClass.CRYPTO
        assert position.side == PositionSide.LONG
        assert Decimal(position.qty) > 0
    finally:
        if position is None:
            # A check failed before the position was read. Read it now, so the
            # close never asks for more than is held.
            position = _open_position_or_none(ctx)
        if position is not None:
            # Close only what this scenario bought, in case the account already
            # held some. Fees can leave the position a little under the fill.
            qty = min(filled_qty, Decimal(position.qty))
            closing = ctx.trading.close_position(
                CRYPTO_POSITION_SYMBOL, ClosePositionRequest(qty=str(qty))
            )

    assert isinstance(closing, Order)
    assert closing.side == OrderSide.SELL
    sold = _wait_until_filled(ctx, closing)
    assert sold.status == OrderStatus.FILLED
    return {
        "bought": bought,
        "listed": listed[0],
        "position": position,
        "closing": closing,
        "sold": sold,
    }
