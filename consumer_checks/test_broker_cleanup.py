"""Offline regression checks for Broker scenario failure paths."""

from contextlib import contextmanager, nullcontext
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from alpaca.broker.models import ACHRelationship, Order, Transfer
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderStatus
from scenarios import _broker, broker_funding, broker_trading


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
