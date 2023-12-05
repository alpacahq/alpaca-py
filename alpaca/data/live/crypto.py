from alpaca.common.websocket import BaseStream
from typing import Optional, Dict
from alpaca.common.enums import BaseURL
from alpaca.data.enums import CryptoFeed


class CryptoDataStream(BaseStream):
    """
    A WebSocket client for streaming live crypto data.

    See BaseStream for more information on implementation and the methods available.
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
