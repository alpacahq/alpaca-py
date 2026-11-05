"""Startup must wait for a subscription without polling."""

import asyncio
import threading
import time

import msgpack
import pytest
import websockets

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
    assert stream._run is not None

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
            if stream._loop is not None and stream._run is not None:
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
def test_threaded_subscribe_then_stop_never_connects(make_stream, subscribe):
    """A cross-thread stop() right after subscribe() must win even though
    subscribe()'s wakeup is scheduled on the loop first.

    The loop thread is parked while both calls are made, so the waiter can
    only resume once the subscription and the stop are both recorded. stop()
    makes the stop visible synchronously, so the waiter must see it instead
    of connecting on the subscription alone.
    """
    stream = make_stream()
    started = []

    async def fail_if_connected():
        started.append(True)

    stream._start_ws = fail_if_connected

    thread = threading.Thread(target=lambda: asyncio.run(stream._run_forever()))
    thread.start()
    release = threading.Event()
    try:
        for _ in range(100):
            if stream._loop is not None and stream._run is not None:
                break
            threading.Event().wait(0.01)
        else:
            raise AssertionError("waiter never started")

        # Runs only once the waiter has parked, then holds the loop thread
        # until both calls below have returned.
        parked = threading.Event()

        def park():
            parked.set()
            release.wait(timeout=2)

        stream._loop.call_soon_threadsafe(park)
        assert parked.wait(timeout=1)

        subscribe(stream)
        stream.stop()
    finally:
        release.set()
        thread.join(timeout=2)
    assert not thread.is_alive()
    assert started == []
    assert stream._run is None


def test_data_stream_run_can_restart_after_a_completed_run():
    """run()'s own `finally: self.stop()` must not leave a stop recorded
    for the next run() to wrongly consume.

    stop() previously inserted a queue token unconditionally. Once a run
    ends on its own (subscription acked, handler closes the socket), that
    finally-triggered stop() ran against a loop that was already closed,
    yet still queued a token. The next run() then found that stale token
    at the very first subscription check and aborted immediately instead
    of connecting.
    """
    stream = DataStream("endpoint", "key-id", "secret-key")
    stream._handlers["trades"]["AAPL"] = _handler
    connects = []

    class _Socket:
        async def recv(self):
            # End this run the same way a server-initiated close would:
            # a direct stop_ws(), not stream.stop().
            await stream.stop_ws()
            return msgpack.packb([{"T": "subscription", "trades": ["AAPL"]}])

        async def close(self):
            pass

    async def fake_start_ws():
        connects.append(True)
        stream._ws = _Socket()

    async def fake_send_subscribe_msg():
        return None

    stream._start_ws = fake_start_ws
    stream._send_subscribe_msg = fake_send_subscribe_msg

    stream.run()
    # The first run's stop died with its RunState, so the second run()
    # below starts clean.
    assert stream._run is None

    stream.run()
    assert len(connects) == 2


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
def test_late_stop_on_a_finished_run_does_not_poison_next_run(make_stream, subscribe):
    """A stop() that picked up a run just as it was exiting must only ever
    affect that run, never the next one.

    stop() reads the live run once and then signals it, so it can end up
    holding a run that has already finished. Signalling that run must be
    harmless (its loop is gone), and the next run must still connect.
    """
    stream = make_stream()
    subscribe(stream)
    runs = []

    async def fake_start_ws():
        runs.append(stream._run)
        await stream.stop_ws()

    stream._start_ws = fake_start_ws
    if isinstance(stream, DataStream):

        async def fake_send_subscribe_msg():
            return None

        stream._send_subscribe_msg = fake_send_subscribe_msg

    asyncio.run(stream._run_forever())
    first = runs[0]

    # What a late stop() still holding the first run does.
    first.request_stop()
    assert first.wake() is False  # its loop has closed
    # And a stop() that arrives once no run is live is a no-op.
    stream.stop()

    asyncio.run(stream._run_forever())
    assert len(runs) == 2
    assert runs[1] is not first


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
def test_stop_from_the_streams_own_loop_does_not_block(make_stream, subscribe):
    """stop() called on the stream's own loop (e.g. from a handler) must
    return immediately and still stop the run.

    It used to wait on a coroutine scheduled on that same loop, which can't
    run while the caller holds the loop, so it blocked for its full timeout.
    """
    stream = make_stream()
    subscribe(stream)
    elapsed = []

    async def fake_start_ws():
        began = time.monotonic()
        stream.stop()
        elapsed.append(time.monotonic() - began)

    stream._start_ws = fake_start_ws
    if isinstance(stream, DataStream):

        async def fake_send_subscribe_msg():
            return None

        stream._send_subscribe_msg = fake_send_subscribe_msg

    async def run_with_timeout():
        await asyncio.wait_for(stream._run_forever(), timeout=2)

    asyncio.run(run_with_timeout())
    assert len(elapsed) == 1
    assert elapsed[0] < 0.5


def _fake_connect_then_stop(stream, connects):
    async def fake_start_ws():
        connects.append(True)
        await stream.stop_ws()

    stream._start_ws = fake_start_ws
    if isinstance(stream, DataStream):

        async def fake_send_subscribe_msg():
            return None

        stream._send_subscribe_msg = fake_send_subscribe_msg


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
def test_cross_thread_stop_before_the_first_run_starts_is_kept(make_stream, subscribe):
    """A stop() that beats the run's thread to its first line must still stop
    that run, instead of being dropped because no run was live yet.

    Calling stop() before the thread even starts is the extreme of
    ``Thread(target=stream.run).start(); stream.stop()``.
    """
    stream = make_stream()
    subscribe(stream)
    connects = []
    _fake_connect_then_stop(stream, connects)

    stream.stop()

    thread = threading.Thread(target=lambda: asyncio.run(stream._run_forever()))
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert connects == []


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
async def test_stop_after_a_run_ended_does_not_abort_the_next_run(
    make_stream, subscribe
):
    """Once a run has ended, a stop with no live run must not be kept for
    whichever run starts next on the same loop.

    The stream is already stopped at that point, so the stop is redundant;
    keeping it would make the restart below return without connecting.
    """
    stream = make_stream()
    subscribe(stream)
    connects = []
    _fake_connect_then_stop(stream, connects)

    await asyncio.wait_for(stream._run_forever(), timeout=1)
    # Defensive cleanup after the run has already returned.
    await stream.stop_ws()
    stream.stop()

    await asyncio.wait_for(stream._run_forever(), timeout=1)
    assert len(connects) == 2


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
async def test_stop_right_after_creating_a_restart_task_stops_it(
    make_stream, subscribe
):
    """A stop issued right after create_task() for a restart must stop that
    restart, even though the task hasn't run its first line yet.

    The stream has already run once, so a stop with no run reserved would be
    dropped as a stop between runs; calling _run_forever() reserves the run
    so the stop reaches it.
    """
    stream = make_stream()
    subscribe(stream)
    connects = []
    _fake_connect_then_stop(stream, connects)

    await asyncio.wait_for(stream._run_forever(), timeout=1)
    assert len(connects) == 1

    task = asyncio.create_task(stream._run_forever())
    # No await between create_task and stop_ws.
    await stream.stop_ws()

    await asyncio.wait_for(task, timeout=1)
    assert len(connects) == 1


@pytest.mark.parametrize(
    "make_stream",
    [
        lambda: DataStream("endpoint", "key-id", "secret-key"),
        lambda: TradingStream("key-id", "secret-key"),
    ],
    ids=["data", "trading"],
)
def test_stop_reentering_while_the_run_lock_is_held_does_not_deadlock(make_stream):
    """stop() from a signal handler runs on whichever thread the signal
    interrupted, which may be holding _run_lock at that moment.

    Calling stop() with the lock already held by the same thread stands in
    for that; it runs on a helper thread so a regression fails instead of
    hanging the suite.
    """
    stream = make_stream()
    done = threading.Event()

    def reenter():
        with stream._run_lock:
            stream.stop()
        done.set()

    threading.Thread(target=reenter, daemon=True).start()
    assert done.wait(timeout=1)


_STREAMS = [
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
]


@pytest.mark.parametrize("make_stream, subscribe", _STREAMS, ids=["data", "trading"])
def test_cross_thread_stop_interrupts_reconnect_backoff(make_stream, subscribe):
    """stop() from another thread must end a long reconnect backoff promptly
    instead of waiting it out."""
    stream = make_stream()
    subscribe(stream)
    attempted = threading.Event()

    async def failing_start_ws():
        attempted.set()
        raise websockets.WebSocketException("connection rejected")

    stream._start_ws = failing_start_ws
    stream._reconnect_delay = lambda _: 60

    thread = threading.Thread(target=lambda: asyncio.run(stream._run_forever()))
    thread.start()
    try:
        assert attempted.wait(timeout=1)
        stream.stop()
    finally:
        thread.join(timeout=2)
    assert not thread.is_alive()


@pytest.mark.asyncio
@pytest.mark.parametrize("make_stream, subscribe", _STREAMS, ids=["data", "trading"])
async def test_a_run_cancelled_before_it_starts_does_not_break_the_next_run(
    make_stream, subscribe
):
    """Calling _run_forever() reserves a run even if its coroutine never gets
    to run; a later run must still start, connect and be stoppable."""
    stream = make_stream()
    subscribe(stream)
    connects = []
    _fake_connect_then_stop(stream, connects)

    task = asyncio.create_task(stream._run_forever())
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    await asyncio.wait_for(stream._run_forever(), timeout=1)
    assert connects == [True]
    assert stream._run is None


class _StopOnFirstEnter:
    """An RLock that calls stream.stop() on the holding thread right after its
    first acquire, the way a signal handler interrupting that thread would."""

    def __init__(self, stream):
        self._lock = threading.RLock()
        self._stream = stream
        self._fired = False

    def __enter__(self):
        self._lock.acquire()
        if not self._fired:
            self._fired = True
            self._stream.stop()
        return self

    def __exit__(self, *exc):
        self._lock.release()


@pytest.mark.parametrize("make_stream, subscribe", _STREAMS, ids=["data", "trading"])
def test_stop_reentering_during_the_first_reservation_is_honored(
    make_stream, subscribe
):
    """A stop() that re-enters while _run_forever() is reserving the very first
    run must neither deadlock nor be lost: that run must not connect."""
    stream = make_stream()
    subscribe(stream)
    connects = []
    _fake_connect_then_stop(stream, connects)
    stream._run_lock = _StopOnFirstEnter(stream)

    thread = threading.Thread(
        target=lambda: asyncio.run(stream._run_forever()), daemon=True
    )
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert connects == []
