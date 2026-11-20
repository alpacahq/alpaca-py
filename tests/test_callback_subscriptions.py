"""Public subscription methods must not block the loop a stream callback runs on.

A blocking call deadlocks that loop, so asyncio timeouts can't fire there. Each
scenario runs its loop in a daemon thread instead, and a bounded join turns a
regression into a quick failure rather than a hung test run.
"""

import asyncio
import concurrent.futures
import inspect
import json
import logging
import threading

import msgpack
import pytest

from alpaca.common._streaming import send_subscription
from alpaca.data.live import CryptoDataStream
from alpaca.trading.stream import TradingStream

_DEADLOCK_TIMEOUT = 5


def _run_bounded(scenario):
    errors = []

    def target():
        try:
            asyncio.run(scenario())
        except BaseException as e:
            errors.append(e)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(_DEADLOCK_TIMEOUT)
    if thread.is_alive():
        pytest.fail(f"stream loop still blocked after {_DEADLOCK_TIMEOUT}s")
    if errors:
        raise errors[0]


async def _noop(data):
    pass


_STREAMS = [
    pytest.param(
        lambda: CryptoDataStream("test-key", "test-secret"),
        lambda stream: stream.subscribe_quotes(_noop, "BTC/USD"),
        id="data",
    ),
    pytest.param(
        lambda: TradingStream("test-key", "test-secret"),
        lambda stream: stream.subscribe_trade_updates(_noop),
        id="trading",
    ),
]


def test_subscription_changes_from_market_data_callback():
    async def scenario():
        stream = CryptoDataStream("test-key", "test-secret", raw_data=True)
        messages = []
        sent = asyncio.Event()

        class Socket:
            async def send(self, frames):
                payload = frames if isinstance(frames, bytes) else b"".join(frames)
                messages.append(msgpack.unpackb(payload))
                if len(messages) == 2:
                    sent.set()

        async def handler(data):
            stream.subscribe_quotes(_noop, "ETH/USD")
            stream.unsubscribe_quotes("BTC/USD")

        stream.subscribe_quotes(handler, "BTC/USD")
        stream._loop = asyncio.get_running_loop()
        stream._ws = Socket()
        stream._running = True
        await stream._dispatch({"T": "q", "S": "BTC/USD"})
        await asyncio.wait_for(sent.wait(), 2)
        assert messages == [
            {"quotes": ["ETH/USD"], "action": "subscribe"},
            {"action": "unsubscribe", "quotes": ["BTC/USD"]},
        ]
        assert "BTC/USD" not in stream._handlers["quotes"]
        await asyncio.to_thread(stream.subscribe_quotes, _noop, "SOL/USD")
        assert messages[-1]["quotes"] == ["ETH/USD", "SOL/USD"]

    _run_bounded(scenario)


def test_trade_update_subscription_from_trade_update_callback():
    async def scenario():
        stream = TradingStream("test-key", "test-secret", raw_data=True)
        messages = []
        sent = asyncio.Event()

        class Socket:
            async def send(self, message):
                messages.append(json.loads(message))
                sent.set()

        async def handler(data):
            stream.subscribe_trade_updates(_noop)

        stream.subscribe_trade_updates(handler)
        stream._loop = asyncio.get_running_loop()
        stream._ws = Socket()
        stream._running = True
        await stream._dispatch({"stream": "trade_updates", "data": {}})
        await asyncio.wait_for(sent.wait(), 2)
        listen = {"action": "listen", "data": {"streams": ["trade_updates"]}}
        assert messages == [listen]
        assert stream._trade_updates_handler is _noop
        await asyncio.to_thread(stream.subscribe_trade_updates, handler)
        assert messages == [listen, listen]
        assert stream._trade_updates_handler is handler

    _run_bounded(scenario)


@pytest.mark.parametrize("make_stream, subscribe", _STREAMS)
@pytest.mark.parametrize("from_thread", [False, True], ids=["callback", "thread"])
def test_close_cancels_pending_subscription_sends(make_stream, subscribe, from_thread):
    async def scenario():
        stream = make_stream()
        entered, cancelled, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()

        class Socket:
            async def send(self, frames):
                entered.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    cancelled.set()

            async def close(self):
                closed.set()

        stream._loop = asyncio.get_running_loop()
        stream._running = True
        stream._ws = Socket()
        if from_thread:

            def subscribe_until_cancelled():
                with pytest.raises(concurrent.futures.CancelledError):
                    subscribe(stream)

            caller = asyncio.create_task(asyncio.to_thread(subscribe_until_cancelled))
        else:
            subscribe(stream)
        await asyncio.wait_for(entered.wait(), 1)
        await asyncio.wait_for(stream.close(), 1)
        if from_thread:
            await asyncio.wait_for(caller, 1)
        assert cancelled.is_set()
        assert closed.is_set()
        assert not stream._subscription_tasks

    _run_bounded(scenario)


@pytest.mark.parametrize("make_stream, subscribe", _STREAMS)
def test_callback_subscription_errors_are_logged(make_stream, subscribe, caplog):
    async def scenario():
        stream = make_stream()

        class Socket:
            async def send(self, frames):
                raise OSError("send failed")

        stream._loop = asyncio.get_running_loop()
        stream._running = True
        stream._ws = Socket()
        subscribe(stream)
        tasks = tuple(stream._subscription_tasks)
        assert tasks
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), 1)
        assert not stream._subscription_tasks

    _run_bounded(scenario)
    assert "subscription update failed" in caplog.text
    assert "send failed" in caplog.text


@pytest.mark.parametrize("make_stream, subscribe", _STREAMS)
def test_cross_thread_subscription_errors_propagate(make_stream, subscribe, caplog):
    async def scenario():
        stream = make_stream()

        class Socket:
            async def send(self, frames):
                raise OSError("send failed")

        stream._loop = asyncio.get_running_loop()
        stream._running = True
        stream._ws = Socket()
        with pytest.raises(OSError, match="send failed"):
            await asyncio.wait_for(asyncio.to_thread(subscribe, stream), 1)
        assert not stream._subscription_tasks

    _run_bounded(scenario)
    assert "subscription update failed" not in caplog.text


@pytest.mark.parametrize("closed_loop", [False, True], ids=["missing", "closed"])
def test_failed_subscription_scheduling_closes_coroutine(closed_loop):
    loop = asyncio.new_event_loop() if closed_loop else None
    if loop is not None:
        loop.close()
    coroutine = _noop(None)
    tasks = set()
    try:
        with pytest.raises((AttributeError, RuntimeError)):
            send_subscription(coroutine, loop, tasks, logging.getLogger(__name__))
        assert inspect.getcoroutinestate(coroutine) == inspect.CORO_CLOSED
        assert not tasks
    finally:
        coroutine.close()


def test_shutdown_before_subscription_starts_closes_coroutine(monkeypatch):
    queued = threading.Event()
    errors = []
    callers = []
    tasks = set()
    coroutine = _noop(None)

    def subscribe(loop):
        try:
            send_subscription(coroutine, loop, tasks, logging.getLogger(__name__))
        except BaseException as exc:
            errors.append(exc)

    async def scenario():
        loop = asyncio.get_running_loop()
        schedule = loop.call_soon_threadsafe

        def notify_queued(*args, **kwargs):
            handle = schedule(*args, **kwargs)
            queued.set()
            return handle

        monkeypatch.setattr(loop, "call_soon_threadsafe", notify_queued)
        caller = threading.Thread(target=subscribe, args=(loop,), daemon=True)
        callers.append(caller)
        caller.start()
        # Keep the loop busy until the send is queued, then return immediately.
        # asyncio.run cancels the queued task before its coroutine can start.
        assert queued.wait(1)

    try:
        _run_bounded(scenario)
        callers[0].join(1)
        assert not callers[0].is_alive()
        assert len(errors) == 1
        assert isinstance(errors[0], concurrent.futures.CancelledError)
        assert inspect.getcoroutinestate(coroutine) == inspect.CORO_CLOSED
        assert not tasks
    finally:
        coroutine.close()
