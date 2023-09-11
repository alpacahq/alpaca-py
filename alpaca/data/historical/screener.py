from typing import Optional, Union

from alpaca.common.rest import RESTClient

from alpaca.common.enums import BaseURL

from alpaca.data.requests import MarketMoversRequest, MostActivesRequest

from alpaca.data.models.screener import MostActives, Movers

from alpaca.common.types import RawData


class ScreenerClient(RESTClient):
    """
    The REST client for interacting with Alpaca Screener API endpoints.

    Learn more on https://docs.alpaca.markets/reference/mostactives
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        use_basic_auth: bool = False,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:
        """
        Instantiates a Historical Data Client.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers.
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False. This has not been implemented yet.
            url_override (Optional[str], optional): If specified allows you to override the base url the client points
              to for proxy/testing.
        """
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            use_basic_auth=use_basic_auth,
            api_version="v1beta1",
            base_url=url_override if url_override is not None else BaseURL.DATA,
            sandbox=False,
            raw_data=raw_data,
        )

    def get_most_actives(
        self, request_params: MostActivesRequest
    ) -> Union[RawData, MostActives]:
        """Returns most active stocks."""
        response = self.get(
            path="/screener/stocks/most-actives",
            data=request_params.to_request_fields(),
        )
        if self._use_raw_data:
            return response
        return MostActives(**response)

    def get_market_movers(
        self, request_params: MarketMoversRequest
    ) -> Union[RawData, Movers]:
        """Return market movers."""
        response = self.get(
            path=f"/screener/{request_params.market_type.lower()}/movers",
            data=request_params.model_dump(exclude={"market_type"}),
        )
        if self._use_raw_data:
            return response
        return Movers(**response)
