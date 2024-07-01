from typing import Awaitable, Callable, Dict, Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.data.enums import CryptoFeed
from alpaca.data.live.websocket import DataStream
from alpaca.data.models.bars import Bar
from alpaca.data.models.orderbooks import Orderbook
from alpaca.data.models.quotes import Quote
from alpaca.data.models.trades import Trade


class CryptoDataStream(DataStream):
    """
    A WebSocket client for streaming live crypto data.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        feed: CryptoFeed = CryptoFeed.US,
        url_override: Optional[str] = None,
        websocket_params: Optional[Dict] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live cryptocurrency data.

        Args:
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool, optional): Whether to return wrapped data or raw API data. Defaults to False.
            feed (CryptoFeed, optional): Which crypto feed to use. Defaults to US.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
              points to for proxy/testing. Defaults to None.
        """
        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.MARKET_DATA_STREAM.value + "/v1beta3/crypto/" + feed
            ),
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )

    def subscribe_trades(
        self, handler: Callable[[Union[Trade, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to trades.

        Args:
            handler (Callable[[Union[Trade, Dict]], Awaitable[None]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["trades"])

    def subscribe_quotes(
        self, handler: Callable[[Union[Quote, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to quotes

        Args:
            handler (Callable[[Union[Quote, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["quotes"])

    def subscribe_bars(
        self, handler: Callable[[Union[Quote, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to minute bars

        Args:
            handler (Callable[[Union[Quote, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["bars"])

    def subscribe_updated_bars(
        self, handler: Callable[[Union[Bar, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to updated minute bars

        Args:
            handler (Callable[[Union[Bar, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["updatedBars"])

    def subscribe_daily_bars(
        self, handler: Callable[[Union[Bar, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to daily bars

        Args:
            handler (Callable[[Union[Bar, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["dailyBars"])

    def subscribe_orderbooks(
        self, handler: Callable[[Union[Orderbook, Dict]], Awaitable[None]], *symbols
    ) -> None:
        """Subscribe to orderbooks

        Args:
            handler (Callable[[Union[Bar, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["orderbooks"])

    def unsubscribe_trades(self, *symbols: str) -> None:
        """Unsubscribe from trades

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("trades", symbols)

    def unsubscribe_quotes(self, *symbols: str) -> None:
        """Unsubscribe from quotes

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("quotes", symbols)

    def unsubscribe_bars(self, *symbols: str) -> None:
        """Unsubscribe from minute bars

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("bars", symbols)

    def unsubscribe_updated_bars(self, *symbols: str) -> None:
        """Unsubscribe from updated bars

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("updatedBars", symbols)

    def unsubscribe_daily_bars(self, *symbols: str) -> None:
        """Unsubscribe from daily bars

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("dailyBars", symbols)

    def unsubscribe_orderbooks(self, *symbols: str) -> None:
        """Unsubscribe from orderbooks

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("orderbooks", symbols)
