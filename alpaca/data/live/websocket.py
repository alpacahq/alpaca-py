import asyncio
import inspect
import logging
import threading
from collections import defaultdict
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple, Union

import msgpack
import websockets
from pydantic import BaseModel

from alpaca.common.types import RawData
from alpaca.common.utils import (
    get_default_user_agent,
    get_websocket_headers_key,
    reconnect_delay,
)
from alpaca.data.models import (
    Bar,
    News,
    Orderbook,
    Quote,
    Trade,
    TradeCancel,
    TradeCorrection,
    TradingStatus,
)

log = logging.getLogger(__name__)


class _MsgType(str, Enum):
    """Wire ``T`` values for market-data and control frames."""

    TRADE = "t"
    QUOTE = "q"
    ORDERBOOK = "o"
    BAR = "b"
    UPDATED_BAR = "u"
    DAILY_BAR = "d"
    STATUS = "s"
    LULD = "l"
    NEWS = "n"
    CORRECTION = "c"
    CANCEL_ERROR = "x"
    SUBSCRIPTION = "subscription"
    ERROR = "error"


# Recognized market-data frames. Control, unknown, and malformed frames must not
# reset the staleness clock because they aren't dispatched as market data.
_CHANNEL_TYPES = {
    _MsgType.TRADE: "trades",
    _MsgType.QUOTE: "quotes",
    _MsgType.ORDERBOOK: "orderbooks",
    _MsgType.BAR: "bars",
    _MsgType.UPDATED_BAR: "updatedBars",
    _MsgType.DAILY_BAR: "dailyBars",
    _MsgType.STATUS: "statuses",
    _MsgType.LULD: "lulds",
    _MsgType.NEWS: "news",
    _MsgType.CORRECTION: "corrections",
    _MsgType.CANCEL_ERROR: "cancelErrors",
}

# Channels delivered alongside trades; they are never subscribed on their own.
_NON_MARKET_DATA_CHANNELS = ("cancelErrors", "corrections")


def _is_market_data(msg: Dict) -> bool:
    msg_type = msg.get("T")
    if msg_type == _MsgType.NEWS:
        return True
    return msg_type in _CHANNEL_TYPES and "S" in msg


class DataStream:
    """
    A base class for extracting out common functionality for data websockets
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        websocket_params: Optional[Dict] = None,
        data_timeout: Optional[float] = None,
    ) -> None:
        """Creates a new DataStream instance.

        Args:
            endpoint (str): The websocket endpoint to connect to
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool, optional): Whether to return raw API data or parsed data. Defaults to False.
            websocket_params (Optional[Dict], optional): Any websocket connection configuration parameters. Defaults to None.
            data_timeout (Optional[float], optional): Maximum number of seconds to wait without
                receiving market data before treating the connection as stale and forcing a
                reconnect. This detects "connected-but-mute" sockets that the transport-level
                ping/pong keepalive cannot catch. Defaults to ``None`` (disabled), since a
                legitimately quiet subscription (for example news or infrequent bars) would
                otherwise trigger periodic reconnects. Pass a positive number of seconds to
                opt in for subscriptions that are expected to receive frequent data.
        """
        self._endpoint = endpoint
        self._api_key = api_key
        self._secret_key = secret_key
        self._ws = None
        self._running = False
        self._loop = None
        if data_timeout is not None and data_timeout <= 0:
            raise ValueError("data_timeout must be a positive number of seconds")
        self._raw_data = raw_data
        self._data_timeout = data_timeout
        self._data_received = False
        self._reconnect_min_backoff = 1.0
        self._reconnect_max_backoff = 30.0
        # Identifies which run of _run_forever() a stop request applies to.
        # _run_generation is the generation of the run that is currently
        # active, or -- when no run is active -- the generation that will be
        # claimed by whichever run starts next (see _run_forever()). stop()
        # stamps _stop_requested_generation with _run_generation, and every
        # stop check compares generations so a value left over from a run that
        # already exited can't match a later run's (higher) generation.
        #
        # _run_active and _stop_lock close the one window that generation
        # comparison alone cannot: a run retires its generation in its
        # `finally` a few event-loop iterations BEFORE the loop stops, so there
        # is a span where _run_generation already holds the NEXT run's value
        # while loop.is_running() still returns True. A cross-thread stop()
        # landing there would otherwise stamp the next run's generation and
        # make it abort on startup. stop() and _run_forever's start/finally
        # mutate this state only under _stop_lock, and stop() stamps only while
        # _run_active is True, so a stop can never be recorded for a run other
        # than the live one it decided to stop.
        self._run_generation = 0
        self._run_active = False
        self._stop_lock = threading.Lock()
        self._stop_requested_generation: Optional[int] = None
        self._stop_stream_event: Optional[asyncio.Event] = None
        self._subscription_ready: Optional[asyncio.Event] = None
        self._handlers = {channel: {} for channel in _CHANNEL_TYPES.values()}
        self._name = "data"
        self._should_run = True
        self._max_frame_size = 32768

        self._websocket_params = {
            "ping_interval": 10,
            "ping_timeout": 180,
            "max_queue": 1024,
        }

        if websocket_params:
            self._websocket_params = websocket_params

    def _reconnect_delay(self, retries: int) -> float:
        """Computes the delay before the next reconnection attempt.

        Args:
            retries (int): The number of consecutive failed attempts (>= 1).

        Returns:
            float: The number of seconds to wait before retrying.
        """
        return reconnect_delay(
            retries, self._reconnect_min_backoff, self._reconnect_max_backoff
        )

    async def _wait_before_reconnect(self, retries: int) -> None:
        if self._stop_stream_event is None or self._stop_stream_event.is_set():
            return
        try:
            await asyncio.wait_for(
                self._stop_stream_event.wait(),
                timeout=self._reconnect_delay(retries),
            )
        except asyncio.TimeoutError:
            pass

    async def _connect(self) -> None:
        """Attempts to connect to the websocket endpoint.
        If the connection attempt fails a value error is thrown.

        Raises:
            ValueError: Raised if there is an unsuccessful connection
        """

        params = dict(self._websocket_params or {})
        extra_headers = {
            **dict(params.pop("extra_headers", {}) or {}),
            **dict(params.pop("additional_headers", {}) or {}),
            # Protocol/SDK headers always win over caller-supplied values.
            "Content-Type": "application/msgpack",
            "User-Agent": get_default_user_agent(),
        }

        header_key = get_websocket_headers_key()
        connect_kwargs = {
            header_key: extra_headers,
            **params,
        }

        log.info(f"connecting to {self._endpoint}")
        self._ws = await websockets.connect(
            self._endpoint,
            **connect_kwargs,
        )
        r = await self._ws.recv()
        msg = msgpack.unpackb(r)
        if msg[0]["T"] != "success" or msg[0]["msg"] != "connected":
            raise ValueError("connected message not received")

    async def _auth(self) -> None:
        """Authenticates with API keys after a successful connection is established.

        Raises:
            ValueError: Raised if authentication is unsuccessful
        """
        await self._ws.send(
            msgpack.packb(
                {
                    "action": "auth",
                    "key": self._api_key,
                    "secret": self._secret_key,
                }
            )
        )
        r = await self._ws.recv()
        msg = msgpack.unpackb(r)
        if msg[0]["T"] == "error":
            raise ValueError(msg[0].get("msg", "auth failed"))
        if msg[0]["T"] != "success" or msg[0]["msg"] != "authenticated":
            raise ValueError("failed to authenticate")

    async def _start_ws(self) -> None:
        """Starts up the websocket connection. Attempts to connect to wss endpoint
        and then authenticates with API keys.
        """
        await self._connect()
        await self._auth()
        log.info(f"connected to {self._endpoint}")

    async def close(self) -> None:
        """Closes the websocket connection."""
        if self._ws:
            try:
                await self._ws.close()
            finally:
                self._ws = None
                self._running = False
        else:
            self._running = False

    def _mark_stop_requested(self) -> None:
        """Makes a stop visible to any waiter: flips the run flag and
        records the run generation the stop applies to.

        Lock-free on purpose: ``stop_ws()`` calls it on the loop thread, where
        it cannot race ``_run_forever()``'s own generation retirement, and
        ``stop()`` calls it already holding ``_stop_lock`` (so taking the lock
        here would deadlock). Callers that run off the loop thread are
        responsible for serializing against the retirement via ``_stop_lock``.
        """
        self._should_run = False
        self._stop_requested_generation = self._run_generation

    def _stop_requested_for(self, run_generation: Optional[int] = None) -> bool:
        """True if a stop has been requested for the given run generation.

        ``run_generation`` defaults to whatever run is current/next
        (``self._run_generation``), for callers that check outside of an
        actual ``_run_forever()`` run (e.g. tests exercising ``_consume()``
        directly).
        """
        if run_generation is None:
            run_generation = self._run_generation
        return self._stop_requested_generation == run_generation

    async def stop_ws(self) -> None:
        """Signals websocket connection should close by recording a stop request
        for the current run generation."""
        self._mark_stop_requested()
        await self._wake_after_stop()

    async def _wake_after_stop(self) -> None:
        """Sets the asyncio-only wakeups for a stop already made visible by
        stop() (see _mark_stop_requested).

        Does not touch _stop_requested_generation again: _mark_stop_requested()
        already recorded it, and since that write is an idempotent overwrite
        (not a one-shot token), there is nothing here that could be lost or
        duplicated.
        """
        if self._stop_stream_event is not None:
            self._stop_stream_event.set()
        # Event.set() from another thread does not wake this loop.
        self._wake_subscription_wait()
        await asyncio.sleep(0)

    async def _consume(self, run_generation: Optional[int] = None) -> bool:
        """Distributes data from websocket connection to appropriate callbacks.

        Args:
            run_generation (Optional[int]): The generation identifying the
                calling run, as captured by ``_run_forever()``. Used to tell
                a stop meant for this run apart from a stale one left by a
                run that has already exited. Defaults to the current/next
                generation for callers that invoke this outside of an
                actual run.

        Returns:
            bool: True if the loop exited because the connection went stale (no
            market data received within ``data_timeout``) and should be reconnected;
            False if it exited because a stop was requested.
        """
        loop = asyncio.get_running_loop()
        last_data_time = loop.time()
        self._data_received = False
        while True:
            if self._stop_requested_for(run_generation):
                await self.close()
                return False
            else:
                receive_timeout = 5.0
                if self._data_timeout is not None:
                    elapsed = loop.time() - last_data_time
                    if elapsed >= self._data_timeout:
                        log.warning(
                            "no data received on %s stream for %.1fs, reconnecting",
                            self._name,
                            self._data_timeout,
                        )
                        await self.close()
                        return True
                    receive_timeout = min(receive_timeout, self._data_timeout - elapsed)
                try:
                    r = await asyncio.wait_for(self._ws.recv(), receive_timeout)
                    msgs = msgpack.unpackb(r)
                    for msg in msgs:
                        # Only actual market data resets the staleness clock and
                        # counts toward recovery; control frames (subscription
                        # acks, errors) must not, otherwise a subscribed-but-mute
                        # stream would look healthy and the escalating backoff
                        # would never engage.
                        is_market_data = _is_market_data(msg)
                        if msg.get("T") in _CHANNEL_TYPES and not is_market_data:
                            continue
                        if is_market_data:
                            self._data_received = True
                        await self._dispatch(msg)
                        if is_market_data:
                            last_data_time = loop.time()
                except asyncio.TimeoutError:
                    # ws.recv is hanging when no data is received. by using
                    # wait_for we break when no data is received, allowing us
                    # to break the loop when needed
                    pass

    def _cast(self, msg: Dict) -> Union[BaseModel, RawData]:
        """Parses data from websocket message if raw_data is False, otherwise
        returns the raw websocket message.

        Args:
            msg (Dict): The message containing market data

        Returns:
            Union[BaseModel, RawData]: The raw or parsed message
        """
        if self._raw_data:
            return msg
        msg_type = msg.get("T")
        if "t" in msg:
            msg["t"] = msg["t"].to_datetime()
        if msg_type == _MsgType.NEWS:
            msg["created_at"] = msg["created_at"].to_datetime()
            msg["updated_at"] = msg["updated_at"].to_datetime()
            # The API always sends "symbols" (possibly []), but normalize
            # defensively here rather than loosening the shared News model,
            # which is also used by the strict historical REST client.
            msg.setdefault("symbols", [])
            return News(msg)
        if "S" not in msg:
            return msg
        if msg_type == _MsgType.TRADE:
            return Trade(msg["S"], msg)
        if msg_type == _MsgType.QUOTE:
            return Quote(msg["S"], msg)
        if msg_type == _MsgType.ORDERBOOK:
            return Orderbook(msg["S"], msg)
        if msg_type in (_MsgType.BAR, _MsgType.UPDATED_BAR, _MsgType.DAILY_BAR):
            return Bar(msg["S"], msg)
        if msg_type == _MsgType.STATUS:
            return TradingStatus(msg["S"], msg)
        if msg_type == _MsgType.CORRECTION:
            return TradeCorrection(msg["S"], msg)
        if msg_type == _MsgType.CANCEL_ERROR:
            return TradeCancel(msg["S"], msg)
        return msg

    async def _dispatch(self, msg: Dict) -> None:
        """Distributes the message from websocket connection to the appropriate handler.

        Args:
            msg (Dict): The message from the websocket connection
        """
        msg_type = msg.get("T")
        if msg_type == _MsgType.SUBSCRIPTION:
            sub = [f"{k}: {msg.get(k, [])}" for k in self._handlers if msg.get(k)]
            log.info(f'subscribed to {", ".join(sub)}')
            return

        if msg_type == _MsgType.ERROR:
            log.error(f'error: {msg.get("msg")} ({msg.get("code")})')
            return

        if msg_type == _MsgType.NEWS:
            # Missing or empty symbols -> wildcard so unsymbolized/global news
            # still reaches the "*" handler under both raw and parsed modes.
            symbols = msg.get("symbols") or ["*"]
            star_handler_called = False
            handlers_to_call = []
            news = self._cast(msg)
            news_handlers = self._handlers[_CHANNEL_TYPES[_MsgType.NEWS]]
            for symbol in set(symbols):
                if symbol in news_handlers:
                    handler = news_handlers.get(symbol)
                elif not star_handler_called:
                    handler = news_handlers.get("*")
                    star_handler_called = True
                else:
                    handler = None
                if handler:
                    handlers_to_call.append(handler(news))
            if handlers_to_call:
                await asyncio.gather(*handlers_to_call)
            return

        channel = _CHANNEL_TYPES.get(msg_type)
        if not channel:
            return
        symbol = msg.get("S")
        handler = self._handlers[channel].get(symbol, self._handlers[channel].get("*"))
        if handler:
            await handler(self._cast(msg))

    def _subscribe(
        self, handler: Callable, symbols: Tuple[str], handlers: Dict
    ) -> None:
        """Subscribes a coroutine callback function to receive data for a tuple of symbols

        Args:
            handler (Callable): The coroutine callback function to receive data
            symbols (Tuple[str]): The tuple containing the symbols to be subscribed to
            handlers (Dict): The dictionary of coroutine callback functions keyed by symbol
        """
        self._ensure_coroutine(handler)
        for symbol in symbols:
            handlers[symbol] = handler
        self._wake_subscription_wait()
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._send_subscribe_msg(), self._loop
            ).result()

    async def _send_subscribe_msg(self) -> None:
        msg = defaultdict(list)
        for k, v in self._handlers.items():
            if k not in _NON_MARKET_DATA_CHANNELS and v:
                for s in v.keys():
                    msg[k].append(s)
        msg["action"] = "subscribe"
        bs = msgpack.packb(msg)
        frames = (
            bs[i : i + self._max_frame_size]
            for i in range(0, len(bs), self._max_frame_size)
        )
        await self._ws.send(frames)

    def _unsubscribe(self, channel: str, symbols: List[str]) -> None:
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._send_unsubscribe_msg(channel, symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers[channel][symbol]

    async def _send_unsubscribe_msg(self, channel: str, symbols: List[str]) -> None:
        if symbols:
            await self._ws.send(
                msgpack.packb(
                    {
                        "action": "unsubscribe",
                        channel: symbols,
                    }
                )
            )

    def _has_market_subscription(self) -> bool:
        return any(
            handlers
            for channel, handlers in self._handlers.items()
            if channel not in _NON_MARKET_DATA_CHANNELS
        )

    def _wake_subscription_wait(self) -> None:
        """Wake the startup wait from this thread or another one."""
        event = self._subscription_ready
        loop = self._loop
        if event is None or loop is None:
            return
        try:
            if loop.is_running():
                loop.call_soon_threadsafe(event.set)
            else:
                event.set()
        except RuntimeError:
            return

    async def _wait_for_market_subscription(
        self, run_generation: Optional[int] = None
    ) -> bool:
        """Block until a market-data subscription exists.

        Args:
            run_generation (Optional[int]): The generation identifying the
                calling run, as captured by ``_run_forever()``. Defaults to
                the current/next generation for callers that invoke this
                outside of an actual run.

        Returns False when stop was requested first. The wait is an event,
        not a polling sleep, so an idle stream does not stay runnable.
        """
        self._subscription_ready = asyncio.Event()
        while True:
            self._subscription_ready.clear()
            if self._stop_requested_for(run_generation):
                return False
            if self._has_market_subscription():
                return True
            await self._subscription_ready.wait()

    async def _run_forever(self) -> None:
        """Starts event loop for receiving data from websocket connection and handles
        distributing messages
        """
        loop = asyncio.get_running_loop()
        # Publish self._loop and mark the run live together under _stop_lock --
        # before anything can block -- so a cross-thread stop() can never
        # observe the new running loop while _run_active is still False (which
        # would make it drop the stop), while a stop issued for this run even
        # before it starts (e.g. immediately after create_task()) is still seen
        # as targeting it. The matching retirement in `finally` guarantees this
        # generation can never later be mistaken for a stop meant for whichever
        # run starts next.
        with self._stop_lock:
            self._loop = loop
            run_generation = self._run_generation
            self._run_active = True
        try:
            # do not start the websocket connection until we subscribe to something
            if not await self._wait_for_market_subscription(run_generation):
                return
            log.info(f"started {self._name} stream")
            self._should_run = True
            self._stop_stream_event = asyncio.Event()
            self._running = False
            retries = 0
            while True:
                try:
                    if not self._should_run:
                        # when signaling to stop, this is how we break run_forever
                        log.info("{} stream stopped".format(self._name))
                        return
                    if not self._running:
                        log.info("starting {} websocket connection".format(self._name))
                        self._data_received = False
                        await self._start_ws()
                        await self._send_subscribe_msg()
                        self._running = True
                    stale = await self._consume(run_generation)
                    if stale:
                        if self._data_received:
                            retries = 0
                        retries += 1
                        # A reconnect forced by data-staleness hits the same
                        # single-connection / slow-reap window as an error reconnect,
                        # so back off here too instead of reconnecting immediately.
                        # All consecutive reconnect failures share this counter;
                        # actual market data resets it.
                        await self._wait_before_reconnect(retries)
                except websockets.WebSocketException as wse:
                    await self.close()
                    self._running = False
                    if self._data_received:
                        retries = 0
                    retries += 1
                    log.warning(
                        "data websocket error, restarting connection: " + str(wse)
                    )
                    await self._wait_before_reconnect(retries)
                except (asyncio.TimeoutError, OSError) as e:
                    if self._running:
                        # Once the session is up an OSError or timeout comes from
                        # user code (a handler writing to a file, for example), not
                        # from the connection, so report it and keep the socket.
                        log.exception(f"error during websocket communication: {str(e)}")
                        if self._data_received:
                            retries = 0
                    else:
                        # Handshake timeouts, DNS failures, refused or reset
                        # connections are transient and retried below. Reporting
                        # them through the catch-all branch printed a traceback
                        # (with the chained asyncio.CancelledError of the abandoned
                        # handshake) on every retry, so treat them like any other
                        # reconnectable error.
                        await self.close()
                        retries += 1
                        log.warning(
                            "websocket connection error, restarting connection: "
                            + str(e)
                        )
                        await self._wait_before_reconnect(retries)
                except Exception as e:
                    if isinstance(e, ValueError) and "insufficient subscription" in str(
                        e
                    ):
                        await self.close()
                        log.exception(f"error during websocket communication: {str(e)}")
                        return
                    log.exception(f"error during websocket communication: {str(e)}")
                    if not self._running:
                        # Close any half-open socket from a failed connect/auth so
                        # abandoned sessions do not keep consuming the
                        # single-connection slot and cause HTTP 429s.
                        await self.close()
                        retries += 1
                        await self._wait_before_reconnect(retries)
                    elif self._data_received:
                        retries = 0
                finally:
                    await asyncio.sleep(0)
        finally:
            with self._stop_lock:
                # Mark the run no longer able to observe stops BEFORE
                # is_running() flips to False (which only happens a few event
                # loop iterations later) and retire its generation. A
                # cross-thread stop() that wakes in that window now sees
                # _run_active False under this same lock and declines to stamp,
                # instead of recording a stop for the generation the next run()
                # will claim.
                self._run_active = False
                self._run_generation = run_generation + 1
                # A stop recorded for the run that is ending has done its job
                # (the stream is stopping), so drop it; left behind it could
                # match the next run's generation and abort it on startup.
                if self._stop_requested_generation == run_generation:
                    self._stop_requested_generation = None

    def run(self) -> None:
        """Starts up the websocket connection's event loop"""
        try:
            asyncio.run(self._run_forever())
        except KeyboardInterrupt:
            print("keyboard interrupt, bye")
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        """Stops the websocket connection."""
        with self._stop_lock:
            if (
                self._loop is None
                or not self._loop.is_running()
                or not self._run_active
            ):
                # No live run to signal, so do not stamp a stop: _loop is None
                # before the stream has ever run; is_running() is False once
                # the loop has closed (run()'s own finally calls stop() then);
                # and _run_active is False in the window where a run has
                # already retired its generation but the loop has not yet
                # stopped. Recording a stop in any of these cases would wrongly
                # target whichever run starts next.
                return
            # Make the stop visible synchronously, under the lock, before
            # scheduling anything on the loop. A subscribe() immediately
            # followed by stop() from another thread would otherwise schedule
            # the subscription-ready wakeup first and the loop wakeup second;
            # the waiter could then resume and see no stop recorded yet, since
            # nothing has run on the loop to record it. Holding the lock also
            # pins _run_generation to this live run, so the stamp can never
            # land on the generation the next run() will claim.
            self._mark_stop_requested()
        wakeup = self._wake_after_stop()
        try:
            asyncio.run_coroutine_threadsafe(wakeup, self._loop).result(timeout=5)
        except RuntimeError:
            # The loop can finish _run_forever and close between the lock
            # release above and this submission, so the coroutine was never
            # scheduled and must be closed explicitly to avoid a "coroutine was
            # never awaited" warning. The stamp we recorded targets the run
            # that just ended; its own `finally` drops it, so nothing leaks.
            wakeup.close()

    def _ensure_coroutine(self, handler: Callable) -> None:
        """Checks if a method is an asyncio coroutine method

        Args:
            handler (Callable): A method to be checked for coroutineness

        Raises:
            ValueError: Raised if the input method is not a coroutine
        """
        if not inspect.iscoroutinefunction(handler):
            raise ValueError("handler must be a coroutine function")
