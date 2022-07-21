from typing import Optional, Dict

from alpaca.common.enums import BaseURL
from alpaca.common.websocket import BaseStream
from alpaca.data.enums import DataFeed


class StockDataStream(BaseStream):
    """
    A WebSocket client for streaming live stock data via IEX or SIP depending on your market data
    subscription.

    See BaseStream for more information on implementation and the methods available.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        feed: DataFeed = DataFeed.IEX,
        websocket_params: Optional[Dict] = None,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live stock data.

        Args:
            api_key (str): Alpaca API key. Defaults to None.
            secret_key (str): Alpaca API secret key. Defaults to None.
            raw_data (bool, optional): Whether to return wrapped data or raw API data. Defaults to False.
            feed (DataFeed, optional): Which market data feed to use; IEX or SIP. Defaults to IEX.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
              points to for proxy/testing. Defaults to None.

        Raises:
            ValueError: Only IEX or SIP market data feeds are supported
        """
        if feed == DataFeed.OTC:
            raise ValueError("OTC not supported for live data feeds")

        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.MARKET_DATA_LIVE.value + "/v2/" + feed.value
            ),
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )
