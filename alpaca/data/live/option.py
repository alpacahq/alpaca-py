from typing import Awaitable, Callable, Dict, Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.data.enums import OptionsFeed
from alpaca.data.live.websocket import DataStream
from alpaca.data.models.quotes import Quote
from alpaca.data.models.trades import Trade


class OptionDataStream(DataStream):
    """
    A WebSocket client for streaming live option data.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        feed: OptionsFeed = OptionsFeed.INDICATIVE,
        websocket_params: Optional[Dict] = None,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live option data.

        Args:
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool): Whether to return wrapped data or raw API data. Defaults to False.
            feed (OptionsFeed): The source feed of the data. `opra` or `indicative`.
                Defaults to `indicative`. `opra` requires a subscription.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket
                connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
                points to for proxy/testing. Defaults to None.
        """
        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.MARKET_DATA_STREAM.value + "/v1beta1/" + feed.value
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
            handler (Callable[[Union[Trade, Dict]], Awaitable[None]]): The coroutine callback
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
