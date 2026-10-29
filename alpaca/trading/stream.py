import asyncio
import inspect
import json
import logging
import threading
from typing import Callable, Dict, Optional, Union

import websockets
from pydantic import BaseModel

from alpaca.common import RawData
from alpaca.common.enums import BaseURL
from alpaca.common.utils import (
    get_default_user_agent,
    get_websocket_headers_key,
    reconnect_delay,
)
from alpaca.trading import TradeUpdate

log = logging.getLogger(__name__)


class TradingStream:
    """
    This is a WebSocket client which allows you to streaming data from your trading account.

    Learn more here: https://alpaca.markets/docs/api-references/trading-api/streaming/

    If using paper keys, make sure to set ``paper`` to True when instantiating the client.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        raw_data: bool = False,
        url_override: str = None,
        websocket_params: Optional[Dict] = None,
    ):
        self._api_key = api_key
        self._secret_key = secret_key
        self._trade_updates_handler = None
        self._endpoint = (
            url_override
            if url_override
            else BaseURL.TRADING_STREAM_PAPER if paper else BaseURL.TRADING_STREAM_LIVE
        )
        self._ws = None
        self._running = False
        self._loop = None
        self._raw_data = raw_data
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
        self._should_run = True
        self._data_received = False
        self._reconnect_min_backoff = 1.0
        self._reconnect_max_backoff = 30.0
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

    async def _connect(self):
        params = dict(self._websocket_params or {})
        extra_headers = {
            **dict(params.pop("extra_headers", {}) or {}),
            **dict(params.pop("additional_headers", {}) or {}),
            "User-Agent": get_default_user_agent(),
        }

        header_key = get_websocket_headers_key()
        connect_kwargs = {
            header_key: extra_headers,
            **params,
        }

        self._ws = await websockets.connect(
            self._endpoint,
            **connect_kwargs,
        )

    async def _auth(self):
        await self._ws.send(
            json.dumps(
                {
                    "action": "authenticate",
                    "data": {
                        "key_id": self._api_key,
                        "secret_key": self._secret_key,
                    },
                }
            )
        )
        r = await self._ws.recv()
        msg = json.loads(r)
        if msg.get("data").get("status") != "authorized":
            raise ValueError("failed to authenticate")

    async def _dispatch(self, msg: Dict) -> None:
        """Distributes message from websocket connection to appropriate handler

        Args:
            msg (Dict): The message from the websocket connection
        """
        stream = msg.get("stream")
        if stream == "trade_updates":
            if self._trade_updates_handler:
                await self._trade_updates_handler(self._cast(msg))

    def _cast(self, msg: Dict) -> Union[BaseModel, RawData]:
        """Parses data from websocket message if raw_data is False, otherwise
        returns raw websocket message

        Args:
            msg (Dict): The message containing market data

        Returns:
            Union[BaseModel, RawData]: The raw or parsed live data
        """
        result = msg
        if not self._raw_data:
            result = TradeUpdate(**msg.get("data"))
        return result

    async def _subscribe_trade_updates(self) -> None:
        if self._trade_updates_handler:
            await self._ws.send(
                json.dumps({"action": "listen", "data": {"streams": ["trade_updates"]}})
            )

    def subscribe_trade_updates(self, handler: Callable):
        """
        Subscribes to trade updates for your trading account.

        Args:
            handler (Callable): The async handler that will receive trade update data.

        Returns:
            None
        """
        self._ensure_coroutine(handler)
        self._trade_updates_handler = handler
        self._wake_subscription_wait()
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._subscribe_trade_updates(), self._loop
            ).result()

    async def _start_ws(self):
        await self._connect()
        await self._auth()
        log.info(f"connected to: {self._endpoint}")
        await self._subscribe_trade_updates()

    async def _consume(self, run_generation: Optional[int] = None):
        while True:
            if self._stop_requested_for(run_generation):
                await self.close()
                break
            else:
                try:
                    r = await asyncio.wait_for(self._ws.recv(), 5)
                    msg = json.loads(r)
                    if msg.get("stream") == "trade_updates":
                        self._data_received = True
                    await self._dispatch(msg)
                except asyncio.TimeoutError:
                    # ws.recv is hanging when no data is received. by using
                    # wait_for we break when no data is received, allowing us
                    # to break the loop when needed
                    pass

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

    async def _wait_for_trade_subscription(
        self, run_generation: Optional[int] = None
    ) -> bool:
        """Block until a trade-update handler is registered.

        Args:
            run_generation (Optional[int]): The generation identifying the
                calling run, as captured by ``_run_forever()``. Defaults to
                the current/next generation for callers that invoke this
                outside of an actual run.

        Returns False when stop was requested first. The wait is an event,
        not a 100ms poll.
        """
        self._subscription_ready = asyncio.Event()
        while True:
            self._subscription_ready.clear()
            if self._stop_requested_for(run_generation):
                return False
            if self._trade_updates_handler:
                return True
            await self._subscription_ready.wait()

    async def _run_forever(self):
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
            if not await self._wait_for_trade_subscription(run_generation):
                return
            log.info("started trading stream")
            self._should_run = True
            self._stop_stream_event = asyncio.Event()
            self._running = False
            retries = 0
            while True:
                try:
                    if not self._should_run:
                        log.info("Trading stream stopped")
                        return
                    if not self._running:
                        log.info("starting trading websocket connection")
                        self._data_received = False
                        await self._start_ws()
                        self._running = True
                    await self._consume(run_generation)
                except websockets.WebSocketException as wse:
                    await self.close()
                    self._running = False
                    if self._data_received:
                        retries = 0
                    retries += 1
                    log.warning(
                        "trading stream websocket error, restarting connection: "
                        + str(wse)
                    )
                    await self._wait_before_reconnect(retries)
                except (asyncio.TimeoutError, OSError) as e:
                    if self._running:
                        # Once the session is up an OSError or timeout comes from
                        # user code (a handler writing to a file, for example), not
                        # from the connection, so report it and keep the socket.
                        log.exception(
                            "error during websocket communication: {}".format(str(e))
                        )
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
                            "trading stream websocket connection error, restarting connection: "
                            + str(e)
                        )
                        await self._wait_before_reconnect(retries)
                except Exception as e:
                    log.exception(
                        "error during websocket communication: {}".format(str(e))
                    )
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
                    await asyncio.sleep(0.01)
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

    def run(self) -> None:
        """Starts up the websocket connection's event loop"""
        try:
            asyncio.run(self._run_forever())
        except KeyboardInterrupt:
            print("keyboard interrupt, bye")
            pass

    def _ensure_coroutine(self, handler: Callable) -> None:
        """Checks if a method is an asyncio coroutine method

        Args:
            handler (Callable): A method to be checked for coroutineness

        Raises:
            ValueError: Raised if the input method is not a coroutine
        """
        if not inspect.iscoroutinefunction(handler):
            raise ValueError("handler must be a coroutine function")
