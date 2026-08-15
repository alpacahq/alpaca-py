from typing import Awaitable, Callable, Dict, Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.data.live.websocket import DataStream
from alpaca.data.models.news import News


class NewsDataStream(DataStream):
    """
    A WebSocket client for streaming news.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        websocket_params: Optional[Dict] = None,
        url_override: Optional[str] = None,
        data_timeout: Optional[float] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live news.
        Args:
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool): Whether to return wrapped data or raw API data. Defaults to False.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket
                connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
                points to for proxy/testing. Defaults to None.
            data_timeout (Optional[float], optional): Maximum number of seconds to wait without
                receiving market data before treating the connection as stale and forcing a
                reconnect. Detects "connected-but-mute" sockets. Defaults to ``None``
                (disabled) because news is typically sparse; pass a positive value to enable.
        """
        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.MARKET_DATA_STREAM.value + "/v1beta1/news"
            ),
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
            data_timeout=data_timeout,
        )

    def subscribe_news(
        self, handler: Callable[[Union[News, Dict]], Awaitable[None]], *symbols: str
    ) -> None:
        """Subscribe to news

        Args:
            handler (Callable[[Union[News, Dict]], Awaitable[None]]): The coroutine callback
                function to handle the incoming data.
            *symbols: List of ticker symbols to subscribe to. "*" for everything.
        """
        self._subscribe(handler, symbols, self._handlers["news"])

    def unsubscribe_news(self, *symbols: str) -> None:
        """Unsubscribe from news

        Args:
            *symbols (str): List of ticker symbols to unsubscribe from. "*" for everything.
        """
        self._unsubscribe("news", symbols)
