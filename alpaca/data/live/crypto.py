from alpaca.common.websocket import BaseStream
from typing import Optional, Dict
from alpaca.common.enums import BaseURL


class CryptoDataStream(BaseStream):
    """
    A WebSocket client for streaming live crypto data.

    See BaseStream for more information on implementation and the methods available.
    """

    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
        raw_data: bool = False,
        websocket_params: Optional[Dict] = None,
    ) -> None:
        """
        Instantiates a WebSocket client for accessing live cryptocurrency data.

        Args:
            api_key (str): Alpaca API key. Defaults to None.
            secret_key (str): Alpaca API secret key. Defaults to None.
            raw_data (bool, optional): Whether to return wrapped data or raw API data. Defaults to False.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.
        """
        super().__init__(
            endpoint=BaseURL.MARKET_DATA_LIVE.value + "/v1beta1/crypto",
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )
