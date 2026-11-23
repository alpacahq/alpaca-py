"""Offline regression checks for Broker scenario failure paths."""

from contextlib import contextmanager, nullcontext
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from alpaca.broker.models import (
    ACHRelationship,
    Order,
    Portfolio,
    Subscription,
    Transfer,
)
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderStatus
from scenarios import _broker, broker_funding, broker_rebalancing, broker_trading


@pytest.mark.parametrize("withdraw_fails", [False, True])
def test_funding_failure_withdraws_before_deleting_relationship_and_closing(
    monkeypatch, withdraw_fails
):
    account_id, relationship_id = uuid4(), uuid4()
    calls = Mock()
    ctx = SimpleNamespace(broker=calls)
    original_error = RuntimeError("listing failed after funding")
    calls.get_ach_relationships_for_account.side_effect = original_error
    calls.withdraw.side_effect = (
        APIError('{"message":"withdrawal failed"}') if withdraw_fails else None
    )
    relationship = ACHRelationship.model_construct(
        id=relationship_id, nickname="consumer-check", status="APPROVED"
    )

    @contextmanager
    def opened_account(ctx, label):
        try:
            yield SimpleNamespace(
                account=SimpleNamespace(id=account_id), wait_until_ready=Mock()
            )
        finally:
            calls.close_account(account_id)

    monkeypatch.setattr(broker_funding, "opened_account", opened_account)
    monkeypatch.setattr(
        broker_funding,
        "fund_with_ach",
        Mock(return_value=(relationship, Transfer.model_construct())),
    )
    monkeypatch.setattr(_broker, "withdraw_remaining_cash", calls.withdraw)

    warning = (
        pytest.warns(UserWarning, match="could not withdraw cash")
        if withdraw_fails
        else nullcontext()
    )
    with warning, pytest.raises(RuntimeError) as raised:
        broker_funding.ach_bank_and_transfer(ctx)

    assert raised.value is original_error
    assert [call[0] for call in calls.mock_calls] == [
        "get_ach_relationships_for_account",
        "withdraw",
        "delete_ach_relationship_for_account",
        "close_account",
    ]
    calls.withdraw.assert_called_once_with(ctx, account_id, relationship_id)
    calls.delete_ach_relationship_for_account.assert_called_once_with(
        account_id, relationship_id
    )


def test_failed_deposit_deletes_the_relationship_it_created():
    account_id, relationship_id = uuid4(), uuid4()
    ctx = SimpleNamespace(broker=Mock())
    ctx.broker.create_ach_relationship_for_account.return_value = (
        ACHRelationship.model_construct(id=relationship_id)
    )
    original_error = APIError('{"message":"transfer failed"}')
    ctx.broker.create_transfer_for_account.side_effect = original_error

    with pytest.raises(APIError) as raised:
        _broker.fund_with_ach(ctx, account_id)

    assert raised.value is original_error
    ctx.broker.delete_ach_relationship_for_account.assert_called_once_with(
        account_id, relationship_id
    )


@pytest.mark.parametrize(
    "withdraw_error, delete_error",
    [
        (AssertionError("cash was not a number"), None),
        (None, APIError('{"message":"delete failed"}')),
        (AssertionError("cash was not a number"), RuntimeError("delete failed")),
    ],
)
def test_release_keeps_the_scenario_error(monkeypatch, withdraw_error, delete_error):
    account_id, relationship_id = uuid4(), uuid4()
    ctx = SimpleNamespace(broker=Mock())
    ctx.broker.delete_ach_relationship_for_account.side_effect = delete_error
    monkeypatch.setattr(
        _broker, "withdraw_remaining_cash", Mock(side_effect=withdraw_error)
    )
    original_error = RuntimeError("scenario failed")

    with pytest.warns(UserWarning), pytest.raises(RuntimeError) as raised:
        try:
            raise original_error
        finally:
            _broker.release_ach_quietly(ctx, account_id, relationship_id)

    assert raised.value is original_error
    ctx.broker.delete_ach_relationship_for_account.assert_called_once_with(
        account_id, relationship_id
    )


def test_rebalancing_failure_unsubscribes_before_closing(monkeypatch):
    account_id, portfolio_id, subscription_id = uuid4(), uuid4(), uuid4()
    calls = Mock()
    ctx = SimpleNamespace(broker=calls, unique_id=lambda label: "0" * 32)
    calls.create_portfolio.return_value = Portfolio.model_construct(id=portfolio_id)
    calls.get_portfolio_by_id.return_value = Portfolio.model_construct(id=portfolio_id)
    calls.update_portfolio_by_id.return_value = Portfolio.model_construct(
        id=portfolio_id, name="consumer-check-000000000000-renamed"
    )
    calls.get_all_portfolios.return_value = [Portfolio.model_construct(id=portfolio_id)]
    calls.create_subscription.return_value = Subscription.model_construct(
        id=subscription_id
    )
    original_error = RuntimeError("subscription lookup failed")
    calls.get_subscription_by_id.side_effect = original_error
    calls.inactivate_portfolio_by_id.side_effect = APIError(
        '{"message":"inactivate failed"}'
    )

    @contextmanager
    def opened_account(ctx, label):
        try:
            yield SimpleNamespace(
                account=SimpleNamespace(id=account_id), wait_until_ready=Mock()
            )
        finally:
            calls.close_account(account_id)

    monkeypatch.setattr(broker_rebalancing, "opened_account", opened_account)

    with pytest.warns(UserWarning, match="inactivate"), pytest.raises(
        RuntimeError
    ) as raised:
        broker_rebalancing.portfolio_subscription_and_run(ctx)

    assert raised.value is original_error
    order = [call[0] for call in calls.mock_calls]
    assert order.index("unsubscribe_account") < order.index("close_account")
    assert order.index("close_account") < order.index("inactivate_portfolio_by_id")
    calls.unsubscribe_account.assert_called_once_with(subscription_id)


@pytest.mark.parametrize("accepted_on_last_poll", [False, True])
def test_order_acceptance_at_polling_deadline(accepted_on_last_poll):
    order_id, account_id = uuid4(), uuid4()
    pending = Order.model_construct(id=order_id, status=OrderStatus.PENDING_NEW)
    accepted = Order.model_construct(id=order_id, status=OrderStatus.NEW)
    ctx = SimpleNamespace(broker=Mock(), sleep=Mock())
    ctx.broker.get_order_for_account_by_id.side_effect = [
        pending,
        accepted if accepted_on_last_poll else pending,
    ]

    if accepted_on_last_poll:
        assert (
            broker_trading._wait_until_accepted(ctx, account_id, pending, attempts=2)
            is accepted
        )
    else:
        with pytest.raises(AssertionError, match="after 2 polls"):
            broker_trading._wait_until_accepted(ctx, account_id, pending, attempts=2)

    assert ctx.sleep.call_count == 2
