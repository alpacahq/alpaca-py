from typing import Optional, Dict

from alpaca.common.enums import BaseURL
from alpaca.common.websocket import BaseStream
from alpaca.data.enums import DataFeed


class NewsDataStream(BaseStream):
    """
    A WebSocket client for streaming live news feed from alpaca data api.

    See BaseStream for more information on implementation and the methods available.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        feed: DataFeed = DataFeed.NEWS,
        websocket_params: Optional[Dict] = None,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live news data.

        Args:
            api_key (str): Alpaca API key.
            secret_key (str): Alpaca API secret key.
            raw_data (bool, optional): Whether to return wrapped data or raw API data. Defaults to False.
            feed (DataFeed, optional): Which news data feed to use. Defaults to News
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
              points to for proxy/testing. Defaults to None.

        Raises:
            ValueError: Only News market data feeds are supported
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
