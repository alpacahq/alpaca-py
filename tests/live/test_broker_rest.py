"""Read-only live BrokerClient smoke tests (sandbox by default)."""

import pytest


@pytest.mark.live
def test_get_clock(broker_client_live, live_call):
    clock = live_call("get_clock", broker_client_live.get_clock)
    assert clock is not None


@pytest.mark.live
def test_get_calendar(broker_client_live, live_call):
    calendar = live_call(
        "get_calendar",
        broker_client_live.get_calendar,
        response_transform=lambda c: c[:5] if isinstance(c, list) else c,
    )
    assert calendar is not None


@pytest.mark.live
def test_list_accounts(broker_client_live, live_call):
    accounts = live_call(
        "list_accounts",
        broker_client_live.list_accounts,
        response_transform=lambda a: a[:5] if isinstance(a, list) else a,
    )
    assert accounts is not None
