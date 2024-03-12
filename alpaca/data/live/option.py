from typing import Dict, Optional

from alpaca.common.enums import BaseURL
from alpaca.common.websocket import BaseStream
from alpaca.data.enums import OptionsFeed


class OptionDataStream(BaseStream):
    """
    A WebSocket client for streaming live option data.

    See BaseStream for more information on implementation and the methods available.
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
            feed (OptionsFeed): The source feed of the data. `opra` or `indicative`. Defaults to `indicative`
            websocket_params (Optional[Dict], optional): Any parameters for configuring websocket connection. Defaults to None.
            url_override (Optional[str]): If specified allows you to override the base url the client
              points to for proxy/testing. Defaults to None.
        """
        super().__init__(
            endpoint=(
                url_override
                if url_override is not None
                else BaseURL.OPTION_DATA_STREAM.value + "/v1beta1/" + feed.value
            ),
            api_key=api_key,
            secret_key=secret_key,
            raw_data=raw_data,
            websocket_params=websocket_params,
        )
