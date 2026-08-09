import asyncio
import json
import logging
import queue
from typing import Callable, Dict, Optional, Union

import websockets
from pydantic import BaseModel
from websockets.legacy import client as websockets_legacy

from alpaca.common import RawData
from alpaca.common.enums import BaseURL
from alpaca.common.utils import get_default_user_agent
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
        self._subscription_event: Optional[asyncio.Event] = None
        self._raw_data = raw_data
        self._stop_stream_queue = queue.Queue()
        self._should_run = True
        self._websocket_params = {
            "ping_interval": 10,
            "ping_timeout": 180,
            "max_queue": 1024,
        }

        if websocket_params:
            self._websocket_params = websocket_params

    async def _connect(self):
        params = dict(self._websocket_params or {})
        extra_headers = dict(params.pop("extra_headers", {}) or {})
        extra_headers["User-Agent"] = get_default_user_agent()
        self._ws = await websockets_legacy.connect(
            self._endpoint,
            extra_headers=extra_headers,
            **params,
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
        self._signal_state_change()
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._subscribe_trade_updates(), self._loop
            ).result()

    def _signal_state_change(self) -> None:
        """Wake the stream's event loop after a subscription or stop request."""
        if self._loop is None or self._subscription_event is None:
            return
        try:
            self._loop.call_soon_threadsafe(self._subscription_event.set)
        except RuntimeError:
            # The stream loop may have closed concurrently with the caller.
            pass

    async def _wait_for_subscription(self) -> bool:
        """Wait until the trade update handler is registered or the stream is stopped."""
        self._subscription_event = asyncio.Event()
        try:
            while True:
                try:
                    self._stop_stream_queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    return False
                if self._trade_updates_handler:
                    return True
                await self._subscription_event.wait()
                self._subscription_event.clear()
        finally:
            self._subscription_event = None

    async def _start_ws(self):
        await self._connect()
        await self._auth()
        log.info(f"connected to: {self._endpoint}")
        await self._subscribe_trade_updates()

    async def _consume(self):
        while True:
            if not self._stop_stream_queue.empty():
                self._stop_stream_queue.get(timeout=1)
                await self.close()
                break
            else:
                try:
                    r = await asyncio.wait_for(self._ws.recv(), 5)
                    msg = json.loads(r)
                    await self._dispatch(msg)
                except asyncio.TimeoutError:
                    # ws.recv is hanging when no data is received. by using
                    # wait_for we break when no data is received, allowing us
                    # to break the loop when needed
                    pass

    async def _run_forever(self):
        self._loop = asyncio.get_running_loop()
        self._should_run = True
        self._running = False
        # do not start the websocket connection until we subscribe to something
        if not await self._wait_for_subscription():
            self._should_run = False
            return
        log.info("started trading stream")
        while True:
            try:
                if not self._should_run:
                    log.info("Trading stream stopped")
                    return
                if not self._running:
                    log.info("starting trading websocket connection")
                    await self._start_ws()
                    self._running = True
                    await self._consume()
            except websockets.WebSocketException as wse:
                await self.close()
                self._running = False
                log.warning(
                    "trading stream websocket error, restarting "
                    + " connection: "
                    + str(wse)
                )
            except Exception as e:
                log.exception(
                    "error during websocket " "communication: {}".format(str(e))
                )
            finally:
                await asyncio.sleep(0.01)

    async def close(self) -> None:
        """Closes the websocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            self._running = False

    async def stop_ws(self) -> None:
        """Signals websocket connection should close by adding a closing message to the stop_stream_queue"""
        self._should_run = False
        if self._stop_stream_queue.empty():
            self._stop_stream_queue.put_nowait({"should_stop": True})
        self._signal_state_change()

    def stop(self) -> None:
        """Stops the websocket connection."""
        if self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.stop_ws(), self._loop).result()

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
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("handler must be a coroutine function")
