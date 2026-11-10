from typing import Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import RawData
from alpaca.data._generated.models import (
    FixedIncomeLatestPricesResp,
    FixedIncomeLatestQuotesResp,
)
from alpaca.data.requests import (
    FixedIncomeLatestPricesRequest,
    FixedIncomeLatestQuotesRequest,
)


class FixedIncomeClient(RESTClient):
    """
    The REST client for interacting with Alpaca Market Data API fixed income endpoints.
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
        Instantiates a Fixed Income Data Client.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers.
            raw_data (bool, optional): If true, API responses will not be wrapped and raw responses will be returned from
              methods. Defaults to False.
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

    def get_fixed_income_latest_prices(
        self, request_params: FixedIncomeLatestPricesRequest
    ) -> Union[FixedIncomeLatestPricesResp, RawData]:
        """Returns the latest prices for the given fixed income securities.

        Args:
            request_params (FixedIncomeLatestPricesRequest): ISINs to price.

        Returns:
            Union[FixedIncomeLatestPricesResp, RawData]: Prices keyed by ISIN.
        """
        raw = self.get(
            path="/fixed_income/latest/prices",
            data=request_params.to_request_fields(),
        )
        if self._use_raw_data:
            return raw
        return FixedIncomeLatestPricesResp.model_validate(raw)

    def get_fixed_income_latest_quotes(
        self, request_params: FixedIncomeLatestQuotesRequest
    ) -> Union[FixedIncomeLatestQuotesResp, RawData]:
        """Returns the latest quotes for the given fixed income securities.

        Args:
            request_params (FixedIncomeLatestQuotesRequest): ISINs to quote, and an optional trade size.

        Returns:
            Union[FixedIncomeLatestQuotesResp, RawData]: Quotes keyed by ISIN.
        """
        raw = self.get(
            path="/fixed_income/latest/quotes",
            data=request_params.to_request_fields(),
        )
        if self._use_raw_data:
            return raw
        return FixedIncomeLatestQuotesResp.model_validate(raw)
