import asyncio
import inspect
import json
import logging
import threading
from typing import Any, Callable, Coroutine, Dict, Optional, Union

import websockets
from pydantic import BaseModel

from alpaca.common import RawData
from alpaca.common.enums import BaseURL
from alpaca.common.utils import (
    RunState,
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
        # The run reserved by the latest _run_forever() call, or None when no
        # run is reserved or live. Each run owns its stop/wakeup state, so a
        # stop can never leak into a later run (see RunState).
        self._run: Optional[RunState] = None
        # Before the first run is reserved, a stop means "don't start": it is
        # remembered so a stop() racing the thread that calls run() is not
        # lost. Once any run has been reserved, a stop with no run means the
        # stream is already stopped, so it is dropped instead of aborting
        # whichever run starts next. _run_lock makes that check atomic with a
        # reservation; it is reentrant so a stop() from a signal handler that
        # interrupts this thread while it holds the lock can't deadlock.
        self._run_lock = threading.RLock()
        self._started_once = False
        self._stop_before_first_run = False
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

    async def _wait_before_reconnect(self, retries: int, run: RunState) -> None:
        if run.stopping:
            return
        await run.sleep(self._reconnect_delay(retries))

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

    async def _consume(self, run: Optional[RunState] = None):
        if run is None:
            run = self._run or RunState(asyncio.get_running_loop())
        while True:
            if run.stopping:
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
        run = self._run
        if run is not None:
            run.wake()

    async def _wait_for_trade_subscription(self, run: RunState) -> bool:
        """Block until a trade-update handler is registered.

        Args:
            run (RunState): The calling run, as created by ``_run_forever()``.

        Returns False when stop was requested first. The wait is an event,
        not a 100ms poll.
        """
        while True:
            run.changed.clear()
            if run.stopping:
                return False
            if self._trade_updates_handler:
                return True
            await run.changed.wait()

    def _run_forever(self) -> Coroutine[Any, Any, None]:
        """Returns the coroutine that runs the stream until it is stopped.

        Not itself a coroutine function so the run is reserved as soon as this
        is called: a stop() issued right after
        ``create_task(stream._run_forever())``, before the task has run its
        first line, then stops this run instead of being dropped as a stop
        between runs.
        """
        return self._drive_run(self._reserve_run())

    def _reserve_run(self) -> RunState:
        run = RunState()
        with self._run_lock:
            # Publish the run before consuming the pre-start flag, so a stop()
            # that re-enters from a signal handler partway through this block
            # either sets the flag before it is read or finds the run.
            self._run = run
            if self._stop_before_first_run:
                run.request_stop()
                self._stop_before_first_run = False
            self._started_once = True
        return run

    async def _drive_run(self, run: RunState) -> None:
        loop = asyncio.get_running_loop()
        # Binding the loop lets stop() wake this run's waiters; a stop issued
        # before this point is still seen, as every wait checks stopping first.
        run.loop = loop
        self._loop = loop
        try:
            # do not start the websocket connection until we subscribe to something
            if not await self._wait_for_trade_subscription(run):
                return
            log.info("started trading stream")
            self._running = False
            retries = 0
            while True:
                try:
                    if run.stopping:
                        log.info("Trading stream stopped")
                        return
                    if not self._running:
                        log.info("starting trading websocket connection")
                        self._data_received = False
                        await self._start_ws()
                        self._running = True
                    await self._consume(run)
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
                    await self._wait_before_reconnect(retries, run)
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
                        await self._wait_before_reconnect(retries, run)
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
                        await self._wait_before_reconnect(retries, run)
                    elif self._data_received:
                        retries = 0
                finally:
                    await asyncio.sleep(0.01)
        finally:
            # A stop() that already picked up this run only ever touches this
            # run's state, so nothing can leak into the next run.
            if self._run is run:
                self._run = None

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

    async def stop_ws(self) -> None:
        """Signals the websocket connection should close."""
        self.stop()
        await asyncio.sleep(0)

    def stop(self) -> None:
        """Stops the websocket connection.

        Safe to call from any thread, including from a handler running on the
        stream's own loop: it never blocks. It stops the run from the latest
        ``_run_forever()`` call even if that run hasn't begun yet. Called before
        the stream has ever run, it keeps the first run from starting; called
        between runs, it is a no-op, since the stream is already stopped.
        """
        with self._run_lock:
            run = self._run
            if run is None:
                if not self._started_once:
                    self._stop_before_first_run = True
                return
        # The stop is visible as soon as request_stop() returns, so a waiter
        # woken by an earlier subscribe() already sees it when it resumes.
        run.request_stop()
        run.wake()

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
