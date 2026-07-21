"""Tests for the streaming reconnect fixes (issue #740).

These originally reproduced the buggy behavior; they now assert the corrected
behavior after the fixes:

* Silent-but-open data socket: ``DataStream`` gained an opt-in ``data_timeout``
  (default ``None``; pass a positive number of seconds to enable). When set, a
  connected socket that stops delivering data (but still answers transport pings)
  breaks the consume loop and reconnects instead of looping forever with
  ``_running`` stuck True.

* Reconnect backoff: both ``DataStream`` and ``TradingStream`` now reconnect with
  exponential backoff + jitter (``_reconnect_delay``) instead of a fixed ~10ms
  retry, avoiding the HTTP 429 storm on single-connection streams.

"""

import asyncio
import json

import msgpack
import pytest
import websockets

from alpaca.data.enums import DataFeed
from alpaca.data.live.crypto import CryptoDataStream
from alpaca.data.live.news import NewsDataStream
from alpaca.data.live.option import OptionDataStream
from alpaca.data.live.stock import StockDataStream
from alpaca.data.live.websocket import DataStream
from alpaca.trading.stream import TradingStream

# ---------------------------------------------------------------------------
# Fix 1: silent-but-open data socket now triggers a reconnect via data_timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_data_stream_reconnects_on_silent_socket():
    """With ``data_timeout`` set, a mute-but-alive socket breaks the loop.

    ``recv`` repeatedly times out without delivering data while advancing the
    clock a little each call. Once the elapsed silence exceeds ``data_timeout``,
    ``_consume`` closes the socket and returns so ``_run_forever`` can reconnect.
    """
    close_calls = 0

    class MuteSocket:
        def __init__(self):
            self.recv_calls = 0

        async def recv(self):
            self.recv_calls += 1
            await asyncio.sleep(0.01)  # advance the clock; deliver no data
            raise asyncio.TimeoutError

        async def close(self):
            nonlocal close_calls
            close_calls += 1

    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.05)
    stream._ws = MuteSocket()
    stream._running = True

    # Previously this looped forever; now it returns once the staleness
    # threshold is crossed. The outer timeout only guards against regressions.
    stale = await asyncio.wait_for(stream._consume(), timeout=2)

    assert stale is True  # signals _run_forever to reconnect
    assert close_calls == 1
    assert stream._running is False
    assert stream._ws is None


@pytest.mark.asyncio
async def test_data_timeout_shorter_than_receive_poll_interval_is_enforced():
    """The configured timeout is not delayed by the five-second receive poll."""

    class MuteSocket:
        async def recv(self):
            await asyncio.Event().wait()

        async def close(self):
            pass

    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.01)
    stream._ws = MuteSocket()
    stream._running = True

    stale = await asyncio.wait_for(stream._consume(), timeout=0.5)

    assert stale is True


@pytest.mark.asyncio
async def test_slow_handler_does_not_make_active_stream_stale():
    """Callback execution time is excluded from the data-staleness window."""

    class Socket:
        def __init__(self):
            self.recv_calls = 0

        async def recv(self):
            self.recv_calls += 1
            if self.recv_calls == 1:
                return msgpack.packb([{"T": "t", "S": "AAPL"}])
            await stream.stop_ws()
            return msgpack.packb([{"T": "subscription", "trades": ["AAPL"]}])

        async def close(self):
            pass

    stream = DataStream(
        "endpoint", "key-id", "secret-key", raw_data=True, data_timeout=0.02
    )

    async def handler(_):
        await asyncio.sleep(0.04)

    stream._handlers["trades"]["AAPL"] = handler
    stream._ws = Socket()
    stream._running = True

    stale = await asyncio.wait_for(stream._consume(), timeout=1)

    assert stale is False
    assert stream._ws is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "control_message",
    [
        {"T": "subscription", "trades": ["AAPL"]},
        {"T": "error", "code": 400, "msg": "boom"},
        {"T": "heartbeat"},
        {},
        {"T": "t"},
    ],
)
async def test_continuous_control_frames_do_not_hide_stale_data(control_message):
    """Control traffic cannot keep a stream with no market data alive forever."""
    control_frame = msgpack.packb([control_message])

    class ControlOnlySocket:
        async def recv(self):
            await asyncio.sleep(0.005)
            return control_frame

        async def close(self):
            pass

    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.03)
    stream._ws = ControlOnlySocket()
    stream._running = True

    stale = await asyncio.wait_for(stream._consume(), timeout=0.5)

    assert stale is True


@pytest.mark.asyncio
async def test_news_without_symbols_is_dispatched_to_wildcard_handler():
    """News frames may omit symbols; they must still reach the '*' handler."""
    received = []

    class Socket:
        def __init__(self):
            self.recv_calls = 0

        async def recv(self):
            self.recv_calls += 1
            if self.recv_calls == 1:
                return msgpack.packb([{"T": "n", "headline": "global"}])
            await stream.stop_ws()
            return msgpack.packb([{"T": "subscription", "news": ["*"]}])

        async def close(self):
            pass

    stream = DataStream(
        "endpoint", "key-id", "secret-key", raw_data=True, data_timeout=0.05
    )

    async def handler(msg):
        received.append(msg)

    stream._handlers["news"]["*"] = handler
    stream._ws = Socket()
    stream._running = True

    stale = await asyncio.wait_for(stream._consume(), timeout=1)

    assert stale is False
    assert received == [{"T": "n", "headline": "global"}]


@pytest.mark.asyncio
async def test_data_stream_run_forever_reconnects_and_resubscribes_after_stale():
    """End-to-end recovery: a stale session leads to a fresh connect + resubscribe.

    Drives the real ``_run_forever`` loop with a fake connect/consume sequence:
    the first session goes mute (``_consume`` returns True), and the second
    session requests a stop. We assert the loop connected and resubscribed a
    second time (the user-visible recovery).
    """
    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.01)

    async def handler(_):
        pass

    stream._handlers["trades"]["AAPL"] = handler

    connects = 0
    subscribes = 0
    consume_calls = 0

    async def fake_start_ws():
        nonlocal connects
        connects += 1
        stream._ws = object()

    async def fake_send_subscribe_msg():
        nonlocal subscribes
        subscribes += 1

    async def fake_consume():
        nonlocal consume_calls
        consume_calls += 1
        if consume_calls == 1:
            # First session goes mute: close and report a stale exit.
            stream._data_received = False
            await stream.close()
            return True
        # Second session: signal stop so _run_forever exits cleanly.
        await stream.stop_ws()
        return False

    async def fake_close():
        stream._ws = None
        stream._running = False

    stream._start_ws = fake_start_ws
    stream._send_subscribe_msg = fake_send_subscribe_msg
    stream._consume = fake_consume
    stream.close = fake_close

    await asyncio.wait_for(stream._run_forever(), timeout=2)

    # Reconnected and resubscribed after the mute session (recovery happened).
    assert connects == 2
    assert subscribes == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "frames, expect_data_received",
    [
        # Only a subscription ack arrives, then the stream goes mute: the ack is
        # a control frame and must NOT count as market data (so escalation can
        # engage on a subscribed-but-mute stream).
        ([[{"T": "subscription", "trades": ["AAPL"]}]], False),
        # An error control frame likewise does not count as market data.
        ([[{"T": "error", "code": 400, "msg": "boom"}]], False),
        # A real trade after the ack does count as market data.
        (
            [
                [{"T": "subscription", "trades": ["AAPL"]}],
                [{"T": "t", "S": "AAPL"}],
            ],
            True,
        ),
    ],
)
async def test_data_received_tracks_market_data_not_control_frames(
    frames, expect_data_received
):
    """``_data_received`` reflects market data only, not subscription/error acks."""
    encoded = [msgpack.packb(f) for f in frames]

    class Socket:
        def __init__(self):
            self._frames = list(encoded)

        async def recv(self):
            if self._frames:
                return self._frames.pop(0)
            await asyncio.sleep(0.01)  # advance clock; go mute
            raise asyncio.TimeoutError

        async def close(self):
            pass

    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.05)
    stream._ws = Socket()
    stream._running = True

    stale = await asyncio.wait_for(stream._consume(), timeout=2)

    assert stale is True
    assert stream._data_received is expect_data_received


@pytest.mark.asyncio
async def test_subscribed_but_mute_stream_escalates_backoff():
    """A stream that only ever receives the ack then mutes escalates its backoff.

    Each reconnect cycle receives only a subscription ack (no market data), so
    ``_data_received`` stays False and the retry count must keep growing rather
    than resetting to 1 every cycle.
    """
    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.01)

    async def handler(_):
        pass

    stream._handlers["trades"]["AAPL"] = handler

    seen_retries = []
    consume_calls = 0

    async def fake_start_ws():
        stream._ws = object()

    async def fake_send_subscribe_msg():
        pass

    async def fake_consume():
        nonlocal consume_calls
        consume_calls += 1
        # Simulate "subscribe ok, then mute": no market data seen this session.
        stream._data_received = False
        await stream.close()
        return True

    async def fake_close():
        stream._ws = None
        stream._running = False

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 5:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._send_subscribe_msg = fake_send_subscribe_msg
    stream._consume = fake_consume
    stream.close = fake_close
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_data_stream_without_timeout_stays_silent():
    """Explicit ``data_timeout=None`` disables staleness detection.

    Confirms sparse streams can opt out so a legitimately quiet market does not
    force reconnects. A large number of silent receive windows do not close the
    socket; only an injected non-timeout error ends the loop.
    """
    close_calls = 0
    silent_cycles = 50

    class BreakLoop(Exception):
        pass

    class MuteSocket:
        def __init__(self):
            self.recv_calls = 0

        async def recv(self):
            self.recv_calls += 1
            if self.recv_calls > silent_cycles:
                raise BreakLoop
            await asyncio.sleep(0)
            raise asyncio.TimeoutError

        async def close(self):
            nonlocal close_calls
            close_calls += 1

    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=None)
    stream._ws = MuteSocket()
    stream._running = True

    with pytest.raises(BreakLoop):
        await stream._consume()

    assert close_calls == 0
    assert stream._running is True


@pytest.mark.asyncio
async def test_data_stream_surfaces_transport_exception_for_reconnect():
    """A transport error still propagates out of ``_consume`` to the reconnect path."""

    class DeadSocket:
        async def recv(self):
            raise websockets.WebSocketException("connection closed")

        async def close(self):
            pass

    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=None)
    stream._ws = DeadSocket()
    stream._running = True

    with pytest.raises(websockets.WebSocketException):
        await stream._consume()


def test_data_timeout_defaults_and_is_configurable():
    """Staleness detection is opt-in (default ``None``); overrides are honored."""
    default = DataStream("endpoint", "key-id", "secret-key")
    assert default._data_timeout is None

    disabled = DataStream("endpoint", "key-id", "secret-key", data_timeout=None)
    assert disabled._data_timeout is None

    configured = DataStream("endpoint", "key-id", "secret-key", data_timeout=30)
    assert configured._data_timeout == 30

    # All stream clients default to disabled so quiet subscriptions are not
    # reconnected; callers opt in per subscription.
    assert StockDataStream("key-id", "secret-key")._data_timeout is None
    assert CryptoDataStream("key-id", "secret-key")._data_timeout is None
    assert OptionDataStream("key-id", "secret-key")._data_timeout is None
    assert NewsDataStream("key-id", "secret-key")._data_timeout is None

    subclass_streams = [
        StockDataStream("key-id", "secret-key", feed=DataFeed.SIP, data_timeout=45),
        CryptoDataStream("key-id", "secret-key", data_timeout=45),
        OptionDataStream("key-id", "secret-key", data_timeout=45),
        NewsDataStream("key-id", "secret-key", data_timeout=45),
    ]
    for stream in subclass_streams:
        assert stream._data_timeout == 45


@pytest.mark.parametrize("bad_value", [0, -1, -0.5])
def test_data_timeout_rejects_non_positive_values(bad_value):
    """A zero/negative ``data_timeout`` is a misconfiguration and is rejected."""
    with pytest.raises(ValueError):
        DataStream("endpoint", "key-id", "secret-key", data_timeout=bad_value)
    with pytest.raises(ValueError):
        StockDataStream("key-id", "secret-key", data_timeout=bad_value)


# ---------------------------------------------------------------------------
# Fix 2: reconnect uses exponential backoff + jitter (no 429 storm)
# ---------------------------------------------------------------------------


def test_reconnect_delay_grows_and_caps():
    """``_reconnect_delay`` grows exponentially with jitter and caps at the max.

    Bounds hold for any random draw (equal jitter => delay in [capped/2, capped]).
    """
    for stream in (
        DataStream("endpoint", "key-id", "secret-key"),
        TradingStream("key-id", "secret-key"),
    ):
        for retries, capped in [
            (1, 1.0),
            (2, 2.0),
            (3, 4.0),
            (10, 30.0),
            (50, 30.0),
            (1025, 30.0),
        ]:
            delays = [stream._reconnect_delay(retries) for _ in range(50)]
            assert min(delays) >= capped / 2 - 1e-9
            assert max(delays) <= capped + 1e-9

        # Never exceeds the configured cap, regardless of attempt count.
        assert all(stream._reconnect_delay(r) <= 30.0 for r in range(1, 100))


@pytest.mark.asyncio
async def test_trading_stream_reconnect_uses_backoff():
    """Repeated connection failures escalate the backoff instead of storming.

    Deterministic (no wall-clock thresholds): ``_reconnect_delay`` is stubbed to
    record the ``retries`` it is called with and to return no delay, and it stops
    the loop after a fixed number of attempts. We assert the retry counter grows
    monotonically (1, 2, 3, ...) across consecutive failures — i.e. backoff is
    applied and never reset while the connection keeps failing.
    """
    stream = TradingStream("key-id", "secret-key")

    async def handler(_):
        pass

    stream._trade_updates_handler = handler

    async def fake_start_ws():
        raise websockets.WebSocketException("connection rejected (HTTP 429)")

    async def fake_close():
        stream._ws = None
        stream._running = False

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 5:
            self_stop()
        return 0  # no real waiting

    def self_stop():
        stream._should_run = False

    stream._start_ws = fake_start_ws
    stream.close = fake_close
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    # Backoff escalates monotonically with each consecutive failure (no reset,
    # no fixed ~10ms cadence).
    assert seen_retries == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream_type", [DataStream, TradingStream])
async def test_failed_start_closes_half_open_socket(stream_type):
    """Connect/auth ValueErrors must close the socket before backoff retries."""

    async def handler(_):
        pass

    if stream_type is DataStream:
        stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=None)
        stream._handlers["trades"]["AAPL"] = handler
    else:
        stream = TradingStream("key-id", "secret-key")
        stream._trade_updates_handler = handler

    close_calls = 0

    class HalfOpenSocket:
        async def close(self):
            nonlocal close_calls
            close_calls += 1

    async def fake_start_ws():
        # Simulate connect succeeding then auth failing, leaving _ws set.
        stream._ws = HalfOpenSocket()
        raise ValueError("failed to authenticate")

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        # Abandoned sessions must not keep the single-connection slot.
        assert stream._ws is None
        if len(seen_retries) >= 3:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 3]
    assert close_calls == 3
    assert stream._ws is None


@pytest.mark.asyncio
@pytest.mark.parametrize("stream_type", [DataStream, TradingStream])
async def test_post_connect_disconnects_escalate_backoff(stream_type):
    """A connection that drops after authentication still escalates backoff."""

    async def handler(_):
        pass

    if stream_type is DataStream:
        stream = DataStream("endpoint", "key-id", "secret-key")
        stream._handlers["trades"]["AAPL"] = handler

        async def fake_send_subscribe_msg():
            pass

        stream._send_subscribe_msg = fake_send_subscribe_msg
    else:
        stream = TradingStream("key-id", "secret-key")
        stream._trade_updates_handler = handler

    async def fake_start_ws():
        stream._ws = object()

    async def fake_consume():
        raise websockets.WebSocketException("connection dropped after authentication")

    async def fake_close():
        stream._ws = None
        stream._running = False

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 5:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._consume = fake_consume
    stream.close = fake_close
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_trading_listening_ack_does_not_reset_backoff():
    """A control acknowledgement alone does not make the connection healthy."""
    stream = TradingStream("key-id", "secret-key")

    async def handler(_):
        pass

    stream._trade_updates_handler = handler

    class ListeningOnlySocket:
        def __init__(self):
            self._sent_ack = False

        async def recv(self):
            if not self._sent_ack:
                self._sent_ack = True
                return json.dumps(
                    {"stream": "listening", "data": {"streams": ["trade_updates"]}}
                )
            raise websockets.WebSocketException(
                "connection dropped after listening acknowledgement"
            )

        async def close(self):
            pass

    async def fake_start_ws():
        stream._ws = ListeningOnlySocket()

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 5:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_healthy_stale_session_resets_transport_backoff():
    """Receiving market data resets earlier transport-failure retries."""
    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.01)

    async def handler(_):
        pass

    stream._handlers["trades"]["AAPL"] = handler
    start_attempts = 0
    consume_calls = 0

    async def fake_start_ws():
        nonlocal start_attempts
        start_attempts += 1
        if start_attempts <= 2:
            raise websockets.WebSocketException("connection rejected")
        stream._ws = object()

    async def fake_send_subscribe_msg():
        pass

    async def fake_consume():
        nonlocal consume_calls
        consume_calls += 1
        if consume_calls == 1:
            stream._data_received = True
            await stream.close()
            return True
        raise websockets.WebSocketException("connection dropped")

    async def fake_close():
        stream._ws = None
        stream._running = False

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 4:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._send_subscribe_msg = fake_send_subscribe_msg
    stream._consume = fake_consume
    stream.close = fake_close
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 1, 2]


@pytest.mark.asyncio
async def test_healthy_transport_session_resets_stale_backoff():
    """Receiving market data resets earlier stale-session retries."""
    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.01)

    async def handler(_):
        pass

    stream._handlers["trades"]["AAPL"] = handler
    consume_calls = 0

    async def fake_start_ws():
        stream._ws = object()

    async def fake_send_subscribe_msg():
        pass

    async def fake_consume():
        nonlocal consume_calls
        consume_calls += 1
        if consume_calls in (1, 2, 4):
            stream._data_received = False
            await stream.close()
            return True
        stream._data_received = True
        raise websockets.WebSocketException("healthy connection dropped")

    async def fake_close():
        stream._ws = None
        stream._running = False

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 4:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._send_subscribe_msg = fake_send_subscribe_msg
    stream._consume = fake_consume
    stream.close = fake_close
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 1, 2]


@pytest.mark.asyncio
async def test_stale_and_transport_failures_share_backoff():
    """Changing failure modes does not reset backoff without market data."""
    stream = DataStream("endpoint", "key-id", "secret-key", data_timeout=0.01)

    async def handler(_):
        pass

    stream._handlers["trades"]["AAPL"] = handler
    connection_attempts = 0

    async def fake_start_ws():
        nonlocal connection_attempts
        connection_attempts += 1
        if connection_attempts == 4:
            raise websockets.WebSocketException("connection rejected")
        stream._ws = object()

    async def fake_send_subscribe_msg():
        pass

    async def fake_consume():
        stream._data_received = False
        await stream.close()
        return True

    async def fake_close():
        stream._ws = None
        stream._running = False

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        if len(seen_retries) >= 4:
            stream._should_run = False
        return 0

    stream._start_ws = fake_start_ws
    stream._send_subscribe_msg = fake_send_subscribe_msg
    stream._consume = fake_consume
    stream.close = fake_close
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert seen_retries == [1, 2, 3, 4]


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [ValueError, RuntimeError])
@pytest.mark.parametrize("stream_type", [DataStream, TradingStream])
async def test_handler_errors_do_not_apply_reconnect_backoff(error_type, stream_type):
    """Errors on an active socket resume consumption without reconnect backoff."""
    handler_calls = 0
    start_calls = 0

    async def handler(_):
        nonlocal handler_calls
        handler_calls += 1
        if handler_calls <= 3:
            raise error_type("handler failed")
        await stream.stop_ws()

    if stream_type is DataStream:
        stream = DataStream("endpoint", "key-id", "secret-key", raw_data=True)
        stream._handlers["trades"]["AAPL"] = handler

        async def fake_send_subscribe_msg():
            pass

        stream._send_subscribe_msg = fake_send_subscribe_msg
    else:
        stream = TradingStream("key-id", "secret-key", raw_data=True)
        stream._trade_updates_handler = handler

    class Socket:
        async def recv(self):
            if stream_type is DataStream:
                return msgpack.packb([{"T": "t", "S": "AAPL"}])
            return json.dumps({"stream": "trade_updates", "data": {}})

        async def close(self):
            pass

    async def fake_start_ws():
        nonlocal start_calls
        start_calls += 1
        stream._ws = Socket()

    seen_retries = []

    def fake_reconnect_delay(retries):
        seen_retries.append(retries)
        return 0

    stream._start_ws = fake_start_ws
    stream._reconnect_delay = fake_reconnect_delay

    await asyncio.wait_for(stream._run_forever(), timeout=5)

    assert handler_calls == 4
    assert start_calls == 1
    assert seen_retries == []


@pytest.mark.asyncio
@pytest.mark.parametrize("stream_type", [DataStream, TradingStream])
async def test_stop_interrupts_reconnect_backoff(stream_type):
    """Stopping either stream interrupts an in-progress reconnect delay."""

    async def handler(_):
        pass

    if stream_type is DataStream:
        stream = DataStream("endpoint", "key-id", "secret-key")
        stream._handlers["trades"]["AAPL"] = handler
    else:
        stream = TradingStream("key-id", "secret-key")
        stream._trade_updates_handler = handler

    connection_attempted = asyncio.Event()

    async def fake_start_ws():
        connection_attempted.set()
        raise websockets.WebSocketException("connection rejected")

    stream._start_ws = fake_start_ws
    stream._reconnect_delay = lambda _: 60

    run_task = asyncio.create_task(stream._run_forever())
    await asyncio.wait_for(connection_attempted.wait(), timeout=0.5)
    await stream.stop_ws()

    await asyncio.wait_for(run_task, timeout=0.5)


@pytest.mark.parametrize("stream_type", [DataStream, TradingStream])
def test_stream_can_restart_on_a_new_event_loop(stream_type):
    """The stop-aware backoff state is recreated when a stream is run again."""

    async def handler(_):
        pass

    if stream_type is DataStream:
        stream = DataStream("endpoint", "key-id", "secret-key")
        stream._handlers["trades"]["AAPL"] = handler
    else:
        stream = TradingStream("key-id", "secret-key")
        stream._trade_updates_handler = handler

    async def run_once():
        connection_attempted = asyncio.Event()

        async def fake_start_ws():
            connection_attempted.set()
            raise websockets.WebSocketException("connection rejected")

        stream._start_ws = fake_start_ws
        stream._reconnect_delay = lambda _: 60

        run_task = asyncio.create_task(stream._run_forever())
        await asyncio.wait_for(connection_attempted.wait(), timeout=0.5)
        await stream.stop_ws()
        await asyncio.wait_for(run_task, timeout=0.5)

    asyncio.run(run_once())
    asyncio.run(run_once())


@pytest.mark.parametrize("stream_type", [DataStream, TradingStream])
def test_restart_after_backoff_stop_connects_once(stream_type):
    """A stop signal from the prior run is not consumed by the restarted stream."""

    async def handler(_):
        pass

    if stream_type is DataStream:
        stream = DataStream("endpoint", "key-id", "secret-key")
        stream._handlers["trades"]["AAPL"] = handler

        async def fake_send_subscribe_msg():
            pass

        stream._send_subscribe_msg = fake_send_subscribe_msg
    else:
        stream = TradingStream("key-id", "secret-key")
        stream._trade_updates_handler = handler

    async def stop_during_backoff():
        connection_attempted = asyncio.Event()

        async def failing_start_ws():
            connection_attempted.set()
            raise websockets.WebSocketException("connection rejected")

        stream._start_ws = failing_start_ws
        stream._reconnect_delay = lambda _: 60

        run_task = asyncio.create_task(stream._run_forever())
        await asyncio.wait_for(connection_attempted.wait(), timeout=0.5)
        await stream.stop_ws()
        await asyncio.wait_for(run_task, timeout=0.5)

    async def restart_successfully():
        connection_attempts = 0

        class Socket:
            async def recv(self):
                await stream.stop_ws()
                if stream_type is DataStream:
                    return msgpack.packb([{"T": "subscription", "trades": ["AAPL"]}])
                return json.dumps(
                    {"stream": "listening", "data": {"streams": ["trade_updates"]}}
                )

            async def close(self):
                pass

        async def successful_start_ws():
            nonlocal connection_attempts
            connection_attempts += 1
            stream._ws = Socket()

        stream._start_ws = successful_start_ws
        await asyncio.wait_for(stream._run_forever(), timeout=0.5)

        assert connection_attempts == 1

    asyncio.run(stop_during_backoff())
    asyncio.run(restart_successfully())
