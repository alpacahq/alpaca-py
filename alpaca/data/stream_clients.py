from alpaca.common.websocket import BaseStream
from typing import Optional, Dict
from alpaca.common.enums import BaseURL
from .enums import DataFeed


class MarketDataStream(BaseStream):
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        raw_data: bool = False,
        feed: DataFeed = DataFeed.IEX,
        websocket_params: Optional[Dict] = None,
    ) -> None:
        """WebSocket client for accessing live equity data.

        Args:
            api_key (str): Alpaca API key. Defaults to None.
            secret_key (str): Alpaca API secret key. Defaults to None.
            raw_data (bool, optional): Whether to return wrapped data or raw API data. Defaults to False.
            feed (DataFeed, optional): Which market data feed to use; IEX or SIP. Defaults to IEX.
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.

        Raises:
            ValueError: Only IEX or SIP market data feeds are supported
        """
        if feed == DataFeed.OTC:
            raise ValueError("OTC not supported for live data feeds")

        super().__init__(
            endpoint=BaseURL.MARKET_DATA_LIVE.value + "/v2/" + feed.value,
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )


class CryptoDataStream(BaseStream):
    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
        raw_data: bool = False,
        websocket_params: Optional[Dict] = None,
    ) -> None:
        """WebSocket client for accessing live cryptocurrency data.

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
