"""Startup must wait for a subscription without polling."""

import asyncio
import threading

import pytest

from alpaca.data.live.websocket import DataStream
from alpaca.trading.stream import TradingStream


async def _handler(_):
    return None


def _patch_sleep(monkeypatch):
    sleeps = []
    real_sleep = asyncio.sleep

    async def spy(delay=0, result=None):
        sleeps.append(delay)
        return await real_sleep(delay, result)

    monkeypatch.setattr(asyncio, "sleep", spy)
    return sleeps, real_sleep


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_stream",
    [
        lambda: DataStream("endpoint", "key-id", "secret-key"),
        lambda: TradingStream("key-id", "secret-key"),
    ],
)
async def test_idle_startup_does_not_poll_and_stop_skips_connect(
    make_stream, monkeypatch
):
    stream = make_stream()
    sleeps, real_sleep = _patch_sleep(monkeypatch)
    started = []

    async def fail_if_connected():
        started.append(True)

    stream._start_ws = fail_if_connected
    task = asyncio.create_task(stream._run_forever())
    await real_sleep(0.05)

    assert sleeps == []
    assert started == []

    await stream.stop_ws()
    await asyncio.wait_for(task, timeout=1)
    assert started == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_stream, subscribe",
    [
        (
            lambda: DataStream("endpoint", "key-id", "secret-key"),
            lambda stream: stream._subscribe(
                _handler, ("AAPL",), stream._handlers["trades"]
            ),
        ),
        (
            lambda: TradingStream("key-id", "secret-key"),
            lambda stream: stream.subscribe_trade_updates(_handler),
        ),
    ],
    ids=["data", "trading"],
)
async def test_stop_after_subscribe_wins_before_waiter_resumes(make_stream, subscribe):
    stream = make_stream()
    started = []

    async def record_connect():
        started.append(True)
        await stream.stop_ws()

    stream._start_ws = record_connect
    task = asyncio.create_task(stream._run_forever())
    await asyncio.sleep(0)
    assert stream._subscription_ready is not None

    # No await between these, so both land before the parked waiter resumes.
    subscribe(stream)
    await stream.stop_ws()

    await asyncio.wait_for(task, timeout=1)
    assert started == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_stream, subscribe",
    [
        (
            lambda: DataStream("endpoint", "key-id", "secret-key"),
            lambda stream: stream._subscribe(
                _handler, ("AAPL",), stream._handlers["trades"]
            ),
        ),
        (
            lambda: TradingStream("key-id", "secret-key"),
            lambda stream: stream.subscribe_trade_updates(_handler),
        ),
    ],
    ids=["data", "trading"],
)
async def test_stop_queued_before_first_run_is_not_treated_as_stale(
    make_stream, subscribe
):
    """A stop meant for a brand-new run must not be discarded as a leftover
    from a previous run.

    Subscribing before the task is created means the startup wait would
    otherwise resolve immediately, so draining every queued stop on entry
    (instead of only a genuinely stale one) would wrongly let this run
    connect.
    """
    stream = make_stream()
    subscribe(stream)
    started = []

    async def fail_if_connected():
        started.append(True)

    stream._start_ws = fail_if_connected
    task = asyncio.create_task(stream._run_forever())
    # No await between create_task and stop_ws, so the stop is queued
    # before the task's first line of code ever runs, yet it must still
    # be honored as this run's own stop request.
    await stream.stop_ws()

    await asyncio.wait_for(task, timeout=1)
    assert started == []


@pytest.mark.parametrize(
    "make_stream, subscribe",
    [
        (
            lambda: DataStream("endpoint", "key-id", "secret-key"),
            lambda stream: stream._subscribe(
                _handler, ("AAPL",), stream._handlers["trades"]
            ),
        ),
        (
            lambda: TradingStream("key-id", "secret-key"),
            lambda stream: stream.subscribe_trade_updates(_handler),
        ),
    ],
)
def test_subscription_from_another_thread_starts_without_waiting(
    make_stream, subscribe
):
    stream = make_stream()
    started = threading.Event()

    async def fake_start_ws():
        started.set()
        await stream.stop_ws()

    stream._start_ws = fake_start_ws
    if isinstance(stream, DataStream):

        async def fake_send_subscribe_msg():
            return None

        stream._send_subscribe_msg = fake_send_subscribe_msg

    thread = threading.Thread(target=lambda: asyncio.run(stream._run_forever()))
    thread.start()
    try:
        for _ in range(100):
            if stream._loop is not None and stream._subscription_ready is not None:
                break
            threading.Event().wait(0.01)
        subscribe(stream)
        assert started.wait(1)
    finally:
        thread.join(timeout=2)
        if thread.is_alive() and stream._loop is not None and stream._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(stream.stop_ws(), stream._loop)
            try:
                future.result(timeout=2)
            except (Exception, asyncio.CancelledError):
                pass
            thread.join(timeout=2)
    assert not thread.is_alive()
