import asyncio
import logging
import queue
from collections import defaultdict
from typing import Callable, Dict, Optional, Union, Tuple

import msgpack
import websockets
from pydantic import BaseModel

from alpaca.common.types import RawData
from alpaca.data.models import Bar, Quote, Trade

log = logging.getLogger(__name__)


class BaseStream:
    """
    A base class for extracting out common functionality for websockets
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        websocket_params: Optional[Dict] = None,
    ) -> None:
        """_summary_

        Args:
            endpoint (str): The websocket endpoint to connect to
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool, optional): Whether to return raw API data or parsed data. Defaults to False.
            websocket_params (Optional[Dict], optional): Any websocket connection configuration parameters. Defaults to None.
        """
        self._endpoint = endpoint
        self._api_key = api_key
        self._secret_key = secret_key
        self._ws = None
        self._running = False
        self._loop = None
        self._raw_data = raw_data
        self._stop_stream_queue = queue.Queue()
        self._handlers = {
            "trades": {},
            "quotes": {},
            "bars": {},
            "updatedBars": {},
            "dailyBars": {},
        }
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

    async def _connect(self) -> None:
        """Attempts to connect to the websocket endpoint.
        If the connection attempt fails a value error is thrown.

        Raises:
            ValueError: Raised if there is an unsuccessful connection
        """
        self._ws = await websockets.connect(
            self._endpoint,
            extra_headers={"Content-Type": "application/msgpack"},
            **self._websocket_params,
        )
        r = await self._ws.recv()
        msg = msgpack.unpackb(r)
        if msg[0]["T"] != "success" or msg[0]["msg"] != "connected":
            raise ValueError("connected message not received")

    async def _auth(self) -> None:
        """Authenicates with API keys after a successful connection is established.

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
        log.info(f"connected to: {self._endpoint}")

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

    async def _consume(self) -> None:
        """Distributes data from websocket connection to appropriate callbacks"""
        while True:
            if not self._stop_stream_queue.empty():
                self._stop_stream_queue.get(timeout=1)
                await self.close()
                break
            else:
                try:
                    r = await asyncio.wait_for(self._ws.recv(), 5)
                    msgs = msgpack.unpackb(r)
                    for msg in msgs:
                        await self._dispatch(msg)
                except asyncio.TimeoutError:
                    # ws.recv is hanging when no data is received. by using
                    # wait_for we break when no data is received, allowing us
                    # to break the loop when needed
                    pass

    def _cast(self, msg_type: str, msg: Dict) -> Union[BaseModel, RawData]:
        """Parses data from websocket message if raw_data is False, otherwise
        returns raw websocket message

        Args:
            msg_type (str): The type of data contained in messaged. ('t' for trade, 'q' for quote, etc)
            msg (Dict): The message containing market data

        Returns:
            Union[BaseModel, RawData]: The raw or parsed live data
        """
        result = msg
        if not self._raw_data:
            # convert msgpack timestamp to nanoseconds
            if "t" in msg:
                msg["t"] = msg["t"].seconds * int(1e9) + msg["t"].nanoseconds

            if "S" not in msg:
                return msg

            if msg_type == "t":
                result = Trade(msg["S"], msg)

            elif msg_type == "q":
                result = Quote(msg["S"], msg)

            elif msg_type in ("b", "u", "d"):
                result = Bar(msg["S"], msg)

        return result

    async def _dispatch(self, msg: Dict) -> None:
        """Distributes message from websocket connection to appropriate handler

        Args:
            msg (Dict): The message from the websocket connection
        """
        msg_type = msg.get("T")
        symbol = msg.get("S")
        if msg_type == "t":
            handler = self._handlers["trades"].get(
                symbol, self._handlers["trades"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "q":
            handler = self._handlers["quotes"].get(
                symbol, self._handlers["quotes"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "b":
            handler = self._handlers["bars"].get(
                symbol, self._handlers["bars"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "u":
            handler = self._handlers["updatedBars"].get(
                symbol, self._handlers["updatedBars"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "d":
            handler = self._handlers["dailyBars"].get(
                symbol, self._handlers["dailyBars"].get("*", None)
            )
            if handler:
                await handler(self._cast(msg_type, msg))
        elif msg_type == "subscription":
            sub = [f"{k}: {msg.get(k, [])}" for k in self._handlers]
            log.info(f'subscribed to {", ".join(sub)}')
        elif msg_type == "error":
            log.error(f'error: {msg.get("msg")} ({msg.get("code")})')

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
        if self._running:
            asyncio.run_coroutine_threadsafe(self._subscribe_all(), self._loop).result()

    async def _subscribe_all(self) -> None:
        """Subscribes to live data"""
        msg = defaultdict(list)
        for k, v in self._handlers.items():
            if k not in ("cancelErrors", "corrections") and v:
                for s in v.keys():
                    msg[k].append(s)
        msg["action"] = "subscribe"
        bs = msgpack.packb(msg)
        frames = (
            bs[i : i + self._max_frame_size]
            for i in range(0, len(bs), self._max_frame_size)
        )
        await self._ws.send(frames)

    async def _unsubscribe(
        self, trades=(), quotes=(), bars=(), updated_bars=(), daily_bars=()
    ) -> None:
        """Unsubscribes from data for symbols specified by the data type
        we want to subscribe from.

        Args:
            trades (tuple, optional): All symbols to unsubscribe trade data for. Defaults to ().
            quotes (tuple, optional): All symbols to unsubscribe quotes data for. Defaults to ().
            bars (tuple, optional): All symbols to unsubscribe minute bar data for. Defaults to ().
            updated_bars (tuple, optional): All symbols to unsubscribe updated bar data for. Defaults to ().
            daily_bars (tuple, optional): All symbols to unsubscribe daily bar data for. Defaults to ().
        """
        if trades or quotes or bars or updated_bars or daily_bars:
            await self._ws.send(
                msgpack.packb(
                    {
                        "action": "unsubscribe",
                        "trades": trades,
                        "quotes": quotes,
                        "bars": bars,
                        "updatedBars": updated_bars,
                        "dailyBars": daily_bars,
                    }
                )
            )

    async def _run_forever(self) -> None:
        """Starts event loop for receiving data from websocket connection and handles
        distributing messages
        """
        self._loop = asyncio.get_running_loop()
        # do not start the websocket connection until we subscribe to something
        while not any(
            v
            for k, v in self._handlers.items()
            if k not in ("cancelErrors", "corrections")
        ):
            if not self._stop_stream_queue.empty():
                # the ws was signaled to stop before starting the loop so
                # we break
                self._stop_stream_queue.get(timeout=1)
                return
            await asyncio.sleep(0)
        log.info(f"started {self._name} stream")
        self._should_run = True
        self._running = False
        while True:
            try:
                if not self._should_run:
                    # when signaling to stop, this is how we break run_forever
                    log.info("{} stream stopped".format(self._name))
                    return
                if not self._running:
                    log.info("starting {} websocket connection".format(self._name))
                    await self._start_ws()
                    await self._subscribe_all()
                    self._running = True
                await self._consume()
            except websockets.WebSocketException as wse:
                await self.close()
                self._running = False
                log.warning("data websocket error, restarting connection: " + str(wse))
            except Exception as e:
                log.exception(
                    "error during websocket " "communication: {}".format(str(e))
                )
            finally:
                await asyncio.sleep(0)

    def subscribe_trades(self, handler: Callable, *symbols) -> None:
        """Subscribe to trade data for symbol inputs

        Args:
            handler (Callable): The coroutine callback function to handle live trade data
            *symbols: Variable string arguments for ticker identifiers to be subscribed to.
        """
        self._subscribe(handler, symbols, self._handlers["trades"])

    def subscribe_quotes(self, handler: Callable, *symbols) -> None:
        """Subscribe to quote data for symbol inputs

        Args:
            handler (Callable): The coroutine callback function to handle live quote data
            *symbols: Variable string arguments for ticker identifiers to be subscribed to.
        """
        self._subscribe(handler, symbols, self._handlers["quotes"])

    def subscribe_bars(self, handler: Callable, *symbols) -> None:
        """Subscribe to minute bar data for symbol inputs

        Args:
            handler (Callable): The coroutine callback function to handle live minute bar data
            *symbols: Variable string arguments for ticker identifiers to be subscribed to.
        """
        self._subscribe(handler, symbols, self._handlers["bars"])

    def subscribe_updated_bars(self, handler: Callable, *symbols) -> None:
        """Subscribe to updated bar data for symbol inputs

        Args:
            handler (Callable): The coroutine callback function to handle live updated bar data
            *symbols: Variable string arguments for ticker identifiers to be subscribed to.
        """
        self._subscribe(handler, symbols, self._handlers["updatedBars"])

    def subscribe_daily_bars(self, handler: Callable, *symbols) -> None:
        """Subscribe to daily bar data for symbol inputs

        Args:
            handler (Callable): The coroutine callback function to handle live daily bar data
            *symbols: Variable string arguments for ticker identifiers to be subscribed to.
        """
        self._subscribe(handler, symbols, self._handlers["dailyBars"])

    def unsubscribe_trades(self, *symbols) -> None:
        """Unsubscribe from trade data for symbol inputs

        Args:
            *symbols: Variable string arguments for ticker identifiers to be unsubscribed from.
        """
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(trades=symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers["trades"][symbol]

    def unsubscribe_quotes(self, *symbols) -> None:
        """Unsubscribe from quote data for symbol inputs

        Args:
            *symbols: Variable string arguments for ticker identifiers to be unsubscribed from.
        """
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(quotes=symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers["quotes"][symbol]

    def unsubscribe_bars(self, *symbols) -> None:
        """Unsubscribe from minute bar data for symbol inputs

        Args:
            *symbols: Variable string arguments for ticker identifiers to be unsubscribed from."""
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(bars=symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers["bars"][symbol]

    def unsubscribe_updated_bars(self, *symbols) -> None:
        """Unsubscribe from updated bar data for symbol inputs

        Args:
            *symbols: Variable string arguments for ticker identifiers to be unsubscribed from."""
        if self._running:
            asyncio.get_event_loop().run_until_complete(
                self._unsubscribe(updated_bars=symbols)
            )
        for symbol in symbols:
            del self._handlers["updatedBars"][symbol]

    def unsubscribe_daily_bars(self, *symbols) -> None:
        """Unsubscribe from daily bar data for symbol inputs

        Args:
            *symbols: Variable string arguments for ticker identifiers to be unsubscribed from."""
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._unsubscribe(daily_bars=symbols), self._loop
            ).result()
        for symbol in symbols:
            del self._handlers["dailyBars"][symbol]

    def run(self) -> None:
        """Starts up the websocket connection's event loop"""
        try:
            asyncio.run(self._run_forever())
        except KeyboardInterrupt:
            print("keyboard interrupt, bye")
            pass

    def stop(self) -> None:
        """Stops the websocket connection."""
        if self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.stop_ws(), self._loop).result()

    def _ensure_coroutine(self, handler: Callable) -> None:
        """Checks if a method is an asyncio coroutine method

        Args:
            handler (Callable): A method to be checked for coroutineness

        Raises:
            ValueError: Raised if the input method is not a coroutine
        """
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("handler must be a coroutine function")
