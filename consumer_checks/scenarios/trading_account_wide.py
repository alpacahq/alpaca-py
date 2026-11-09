"""Trading API methods that act on the whole paper account.

They cancel every open order, close every position, or change (and then
restore) account settings. That is why the consumer checks use keys of their
own (CONSUMER_TRADING_API_KEY_ID / CONSUMER_TRADING_API_SECRET_KEY) for a paper account used
only by them.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set
from uuid import UUID

from alpaca.trading.enums import (
    OrderSide,
    OrderStatus,
    TimeInForce,
    TradeConfirmationEmail,
)
from alpaca.trading.models import AccountConfiguration, ClosePositionResponse, Order
from alpaca.trading.requests import (
    CancelOrderResponse,
    LimitOrderRequest,
    MarketOrderRequest,
)

from . import Context, scenario

UNFILLABLE_LIMIT_PRICE = 1.00
CRYPTO_SYMBOL = "BTC/USD"
CRYPTO_POSITION_SYMBOL = "BTCUSD"
CRYPTO_NOTIONAL = 10


def _wait_for_status(ctx: Context, order_id: UUID, status: OrderStatus) -> Order:
    order = ctx.trading.get_order_by_id(order_id)
    for _ in range(15):
        assert isinstance(order, Order)
        if order.status == status:
            break
        ctx.sleep(1)
        order = ctx.trading.get_order_by_id(order_id)
    assert isinstance(order, Order)
    return order


def _unfillable_limit_buy(ctx: Context, symbol: str, label: str) -> Order:
    order = ctx.trading.submit_order(
        LimitOrderRequest(
            symbol=symbol,
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=UNFILLABLE_LIMIT_PRICE,
            client_order_id=ctx.unique_id(label),
        )
    )
    assert isinstance(order, Order)
    return order


def _cancel_quietly(ctx: Context, order_ids: Iterable[UUID]) -> None:
    """Failure-path cleanup. Never raises, so the error that sent us here is
    the one reported."""
    for order_id in order_ids:
        try:
            ctx.trading.cancel_order_by_id(order_id)
        except Exception:  # already canceled or filled, or the SDK is broken
            pass


def _close_quietly(ctx: Context, symbol: str) -> None:
    """Failure-path cleanup. Never raises, like _cancel_quietly."""
    try:
        ctx.trading.close_position(symbol)
    except Exception:  # already closed: the close-all may have gone through
        pass


@scenario(covers=["TradingClient.cancel_orders"])
def cancel_all_open_orders(ctx: Context) -> Dict[str, Any]:
    orders: List[Order] = []
    confirmed: Set[UUID] = set()
    try:
        orders.append(_unfillable_limit_buy(ctx, "AAPL", "aapl"))
        orders.append(_unfillable_limit_buy(ctx, "MSFT", "msft"))
        result = ctx.trading.cancel_orders()
        assert isinstance(result, list)
        responses = result
        confirmed = {
            response.id
            for response in responses
            if isinstance(response, CancelOrderResponse)
            and 200 <= response.status < 300
        }
    finally:
        # Cancel every order this scenario created that the cancel-all did not
        # confirm: a step failed, or the response reported a failure for it.
        _cancel_quietly(
            ctx, [order.id for order in orders if order.id not in confirmed]
        )
    ids = {order.id for order in orders}

    assert all(isinstance(response, CancelOrderResponse) for response in responses)
    ours = sorted(
        (response for response in responses if response.id in ids),
        key=lambda response: str(response.id),
    )
    assert {response.id for response in ours} == ids
    # One HTTP status per order: users check it to see which cancels failed.
    assert all(200 <= response.status < 300 for response in ours)

    canceled = [
        _wait_for_status(ctx, order.id, OrderStatus.CANCELED) for order in orders
    ]
    assert all(order.status == OrderStatus.CANCELED for order in canceled)
    return {"responses": ours, "canceled": canceled}


@scenario(covers=["TradingClient.close_all_positions"])
def close_all_positions_and_cancel_orders(ctx: Context) -> Dict[str, Any]:
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
    pending: Optional[Order] = None
    btc_closed = False
    try:
        bought = _wait_for_status(ctx, buy.id, OrderStatus.FILLED)
        if bought.status != OrderStatus.FILLED:
            raise AssertionError(f"market buy did not fill: {bought.status}")
        pending = _unfillable_limit_buy(ctx, "AAPL", "pending")
        # cancel_orders=True also cancels the open AAPL order first.
        result = ctx.trading.close_all_positions(cancel_orders=True)
        assert isinstance(result, list)
        closed = result
        btc = [r for r in closed if r.symbol == CRYPTO_POSITION_SYMBOL]
        btc_closed = len(btc) == 1 and btc[0].status == 200
    finally:
        if not btc_closed:
            # A step failed, or the close-all reported a failure for BTC: undo
            # what this scenario created. The buy may have filled after all, and
            # the close-all may have gone through even if the SDK then failed.
            _cancel_quietly(ctx, [buy.id] + ([pending.id] if pending else []))
            _close_quietly(ctx, CRYPTO_POSITION_SYMBOL)

    assert pending is not None
    assert all(isinstance(response, ClosePositionResponse) for response in closed)
    assert len(btc) == 1
    assert btc[0].status == 200
    closing = btc[0].body
    assert isinstance(closing, Order)
    assert closing.side == OrderSide.SELL
    # The API sends no order_id, so it stays None despite its docstring; the
    # closing order is in body. The snapshot keeps that None.

    sold = _wait_for_status(ctx, closing.id, OrderStatus.FILLED)
    assert sold.status == OrderStatus.FILLED
    canceled = _wait_for_status(ctx, pending.id, OrderStatus.CANCELED)
    assert canceled.status == OrderStatus.CANCELED
    return {"btc": btc[0], "sold": sold, "canceled": canceled}


@scenario(
    covers=[
        "TradingClient.get_account_configurations",
        "TradingClient.set_account_configurations",
    ],
)
def account_configuration_round_trip(ctx: Context) -> Dict[str, Any]:
    # Flips only the trade confirmation email setting, then restores it.
    config = ctx.trading.get_account_configurations()
    assert isinstance(config, AccountConfiguration)
    original = config.trade_confirm_email
    target = (
        TradeConfirmationEmail.NONE
        if original == TradeConfirmationEmail.ALL
        else TradeConfirmationEmail.ALL
    )

    # Models validate on assignment, so this is how users edit a setting.
    config.trade_confirm_email = target
    try:
        updated = ctx.trading.set_account_configurations(config)
        assert isinstance(updated, AccountConfiguration)
        assert updated.trade_confirm_email == target
        assert updated.fractional_trading == config.fractional_trading
    finally:
        config.trade_confirm_email = original
        restored = ctx.trading.set_account_configurations(config)

    assert isinstance(restored, AccountConfiguration)
    assert restored.trade_confirm_email == original
    return {"updated": updated, "restored": restored}
