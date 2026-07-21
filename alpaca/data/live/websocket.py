import asyncio
import logging
import queue
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple, Union

import msgpack
import websockets
from pydantic import BaseModel
from websockets.legacy import client as websockets_legacy

from alpaca import __version__
from alpaca.common.types import RawData
from alpaca.common.utils import reconnect_delay
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

# Recognized market-data frames. Control, unknown, and malformed frames must not
# reset the staleness clock because they aren't dispatched as market data.
_CHANNEL_TYPES = {
    "t": "trades",
    "q": "quotes",
    "o": "orderbooks",
    "b": "bars",
    "u": "updatedBars",
    "d": "dailyBars",
    "s": "statuses",
    "l": "lulds",
    "n": "news",
    "c": "corrections",
    "x": "cancelErrors",
}


def _is_market_data(msg: Dict) -> bool:
    msg_type = msg.get("T")
    if msg_type == "n":
        return "symbols" in msg
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
        self._stop_stream_queue = queue.Queue()
        self._stop_stream_event: Optional[asyncio.Event] = None
        self._handlers = {
            "trades": {},
            "quotes": {},
            "orderbooks": {},
            "bars": {},
            "updatedBars": {},
            "dailyBars": {},
            "statuses": {},
            "lulds": {},
            "news": {},
            "corrections": {},
            "cancelErrors": {},
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

        extra_headers = {
            "Content-Type": "application/msgpack",
            "User-Agent": "APCA-PY/" + __version__,
        }

        log.info(f"connecting to {self._endpoint}")
        self._ws = await websockets_legacy.connect(
            self._endpoint,
            extra_headers=extra_headers,
            **self._websocket_params,
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

    async def stop_ws(self) -> None:
        """Signals websocket connection should close by adding a closing message to the stop_stream_queue"""
        self._should_run = False
        if self._stop_stream_event is not None:
            self._stop_stream_event.set()
        if self._stop_stream_queue.empty():
            self._stop_stream_queue.put_nowait({"should_stop": True})
        await asyncio.sleep(0)

    async def _consume(self) -> bool:
        """Distributes data from websocket connection to appropriate callbacks.

        Returns:
            bool: True if the loop exited because the connection went stale (no
            market data received within ``data_timeout``) and should be reconnected;
            False if it exited because a stop was requested.
        """
        loop = asyncio.get_running_loop()
        last_data_time = loop.time()
        self._data_received = False
        while True:
            if not self._stop_stream_queue.empty():
                self._stop_stream_queue.get(timeout=1)
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
        if msg_type == "n":
            msg["created_at"] = msg["created_at"].to_datetime()
            msg["updated_at"] = msg["updated_at"].to_datetime()
            return News(msg)
        if "S" not in msg:
            return msg
        if msg_type == "t":
            return Trade(msg["S"], msg)
        if msg_type == "q":
            return Quote(msg["S"], msg)
        if msg_type == "o":
            return Orderbook(msg["S"], msg)
        if msg_type in ("b", "u", "d"):
            return Bar(msg["S"], msg)
        if msg_type == "s":
            return TradingStatus(msg["S"], msg)
        if msg_type == "c":
            return TradeCorrection(msg["S"], msg)
        if msg_type == "x":
            return TradeCancel(msg["S"], msg)
        return msg

    async def _dispatch(self, msg: Dict) -> None:
        """Distributes the message from websocket connection to the appropriate handler.

        Args:
            msg (Dict): The message from the websocket connection
        """
        msg_type = msg.get("T")
        if msg_type == "subscription":
            sub = [f"{k}: {msg.get(k, [])}" for k in self._handlers if msg.get(k)]
            log.info(f'subscribed to {", ".join(sub)}')
            return

        if msg_type == "error":
            log.error(f'error: {msg.get("msg")} ({msg.get("code")})')
            return

        if msg_type == "n":
            symbols = msg.get("symbols", "*")
            star_handler_called = False
            handlers_to_call = []
            news = self._cast(msg)
            for symbol in set(symbols):
                if symbol in self._handlers["news"]:
                    handler = self._handlers["news"].get(symbol)
                elif not star_handler_called:
                    handler = self._handlers["news"].get("*")
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
        if self._running:
            asyncio.run_coroutine_threadsafe(
                self._send_subscribe_msg(), self._loop
            ).result()

    async def _send_subscribe_msg(self) -> None:
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
        while not self._stop_stream_queue.empty():
            self._stop_stream_queue.get_nowait()
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
                stale = await self._consume()
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
                log.warning("data websocket error, restarting connection: " + str(wse))
                await self._wait_before_reconnect(retries)
            except Exception as e:
                if isinstance(e, ValueError) and "insufficient subscription" in str(e):
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
        if self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.stop_ws(), self._loop).result(
                timeout=5
            )

    def _ensure_coroutine(self, handler: Callable) -> None:
        """Checks if a method is an asyncio coroutine method

        Args:
            handler (Callable): A method to be checked for coroutineness

        Raises:
            ValueError: Raised if the input method is not a coroutine
        """
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("handler must be a coroutine function")
