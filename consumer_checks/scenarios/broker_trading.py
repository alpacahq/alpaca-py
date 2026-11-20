"""Orders and positions on an account this scenario funds and then closes.

The limit buy is priced at $1, so it cannot fill. Nothing liquidates another
account: close-all and the missing-position calls use this account's id.
"""

from __future__ import annotations

from typing import Any, Dict, cast

from alpaca.broker.models import Order
from alpaca.broker.requests import LimitOrderRequest, OrderRequest
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import (
    OrderSide,
    OrderStatus,
    OrderType,
    QueryOrderStatus,
    TimeInForce,
)
from alpaca.trading.models import ClosePositionResponse, PortfolioHistory, Position
from alpaca.trading.requests import (
    CancelOrderResponse,
    ClosePositionRequest,
    GetOrdersRequest,
    GetPortfolioHistoryRequest,
    ReplaceOrderRequest,
)

from . import Context, scenario
from ._broker import (
    UNFILLABLE_LIMIT_PRICE,
    expect_client_error,
    fund_with_ach,
    opened_account,
    wait_for_buying_power,
    withdraw_quietly,
)
from ._errors import error_details

BROKER = "broker"


def _limit(client_order_id: str, price: float = UNFILLABLE_LIMIT_PRICE) -> OrderRequest:
    # LimitOrderRequest is what users pass. It is a sibling of the broker
    # OrderRequest, not a subclass, so the cast matches the client signature.
    return cast(
        OrderRequest,
        LimitOrderRequest(
            symbol="AAPL",
            qty=1,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=price,
            client_order_id=client_order_id,
        ),
    )


def _wait_until_accepted(
    ctx: Context, account_id: Any, order: Order, attempts: int = 10
) -> Order:
    """An order still in pending_new cannot be replaced yet."""
    current = order
    for _ in range(attempts):
        if current.status != OrderStatus.PENDING_NEW:
            break
        ctx.sleep(1)
        fetched = ctx.broker.get_order_for_account_by_id(account_id, order.id)
        assert isinstance(fetched, Order)
        current = fetched
    if current.status == OrderStatus.PENDING_NEW:
        raise AssertionError(f"order stayed {current.status} after {attempts} polls")
    return current


@scenario(
    covers=[
        "BrokerClient.submit_order_for_account",
        "BrokerClient.get_order_for_account_by_id",
        "BrokerClient.get_order_for_account_by_client_id",
        "BrokerClient.get_orders_for_account",
        "BrokerClient.replace_order_for_account_by_id",
        "BrokerClient.cancel_order_for_account_by_id",
        "BrokerClient.cancel_orders_for_account",
        "BrokerClient.get_all_positions_for_account",
        "BrokerClient.get_open_position_for_account",
        "BrokerClient.close_all_positions_for_account",
        "BrokerClient.close_position_for_account",
        "BrokerClient.get_portfolio_history_for_account",
        "BrokerClient.exercise_options_position_for_account_by_id",
    ],
    credentials=BROKER,
)
def order_and_position_lifecycle(ctx: Context) -> Dict[str, Any]:
    with opened_account(ctx, "trading") as session:
        session.wait_until_ready()
        account_id = session.account.id
        relationship, _transfer = fund_with_ach(ctx, account_id)
        try:
            wait_for_buying_power(ctx, account_id)

            first_id = ctx.unique_id("order")
            second_id = ctx.unique_id("order-2")
            first = ctx.broker.submit_order_for_account(account_id, _limit(first_id))
            second = ctx.broker.submit_order_for_account(account_id, _limit(second_id))
            assert isinstance(first, Order) and isinstance(second, Order)
            assert first.client_order_id == first_id
            assert first.symbol == "AAPL"
            assert first.side == OrderSide.BUY

            by_id = ctx.broker.get_order_for_account_by_id(account_id, first.id)
            by_client = ctx.broker.get_order_for_account_by_client_id(
                account_id, second_id
            )
            assert isinstance(by_id, Order) and isinstance(by_client, Order)
            assert by_id.id == first.id
            assert by_client.id == second.id

            open_orders = ctx.broker.get_orders_for_account(
                account_id,
                GetOrdersRequest(
                    status=QueryOrderStatus.OPEN, symbols=["AAPL"], limit=10
                ),
            )
            assert isinstance(open_orders, list)
            assert {order.id for order in open_orders} >= {first.id, second.id}

            _wait_until_accepted(ctx, account_id, by_id)
            replaced = ctx.broker.replace_order_for_account_by_id(
                account_id,
                first.id,
                ReplaceOrderRequest(
                    limit_price=1.01, client_order_id=ctx.unique_id("replaced")
                ),
            )
            assert isinstance(replaced, Order)
            assert replaced.id != first.id
            assert replaced.limit_price is not None

            ctx.broker.cancel_order_for_account_by_id(account_id, replaced.id)
            canceled = ctx.broker.cancel_orders_for_account(account_id)
            assert isinstance(canceled, list)
            assert all(isinstance(item, CancelOrderResponse) for item in canceled)

            positions = ctx.broker.get_all_positions_for_account(account_id)
            assert isinstance(positions, list)
            assert all(isinstance(position, Position) for position in positions)

            missing_position = expect_client_error(
                lambda: ctx.broker.get_open_position_for_account(account_id, "AAPL")
            )
            closed_all = ctx.broker.close_all_positions_for_account(
                account_id, cancel_orders=True
            )
            assert isinstance(closed_all, list)
            assert all(isinstance(item, ClosePositionResponse) for item in closed_all)
            missing_close = expect_client_error(
                lambda: ctx.broker.close_position_for_account(
                    account_id, "AAPL", ClosePositionRequest(qty="1")
                )
            )

            history = ctx.broker.get_portfolio_history_for_account(
                account_id, GetPortfolioHistoryRequest(period="1W", timeframe="1D")
            )
            assert isinstance(history, PortfolioHistory)

            # The account holds no option. A real exercise cannot be undone.
            exercise = expect_client_error(
                lambda: ctx.broker.exercise_options_position_for_account_by_id(
                    "AAPL240119C00100000",
                    account_id,
                    commission=0,
                    qty="1",
                )
            )
        finally:
            try:
                ctx.broker.cancel_orders_for_account(account_id)
            except APIError:
                pass
            # close_account is refused while the account still holds the deposit.
            withdraw_quietly(ctx, account_id, relationship.id)
            ctx.broker.delete_ach_relationship_for_account(account_id, relationship.id)

    return {
        "replaced": replaced,
        "positions": positions,
        "closed_all": closed_all,
        "history": history,
        "missing_position": error_details(missing_position),
        "missing_close": error_details(missing_close),
        "exercise": error_details(exercise),
    }
