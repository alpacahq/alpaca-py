from typing import Optional, Union

from alpaca.common.enums import BaseURL
from alpaca.common.rest import RESTClient
from alpaca.common.types import Credentials, RawData
from alpaca.data.models.news import NewsSet
from alpaca.data.requests import NewsRequest


class NewsClient(RESTClient):
    """
    The REST client for interacting with Alpaca News API endpoints.

    This client does not require authentication to use.
    You can instantiate it with or without API keys.

    However, authenticating increases your data rate limit.
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

    def get_news(self, request_params: NewsRequest) -> Union[RawData, NewsSet]:
        """Returns news data

        Args:
            request_params (NewsRequest): The request params to filter the news data"""
        raw_news = self._get_marketdata(
            path=f"/news",
            params=request_params.to_request_fields(),
            page_limit=50,
            page_size=50,
        )
        if self._use_raw_data:
            return raw_news

        return NewsSet(raw_news)

    @staticmethod
    def _validate_credentials(
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
    ) -> Credentials:
        if oauth_token and (api_key or secret_key):
            raise ValueError(
                "Either an oauth_token or an api_key may be supplied, but not both"
            )

        if api_key and not secret_key:
            raise ValueError(
                "A corresponding secret_key must be supplied with the api_key"
            )

        if not api_key and secret_key:
            raise ValueError(
                "A corresponding api_key must be supplied with the secret_key"
            )

        return api_key, secret_key, oauth_token
