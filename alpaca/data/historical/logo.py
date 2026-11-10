from typing import Optional

from requests.exceptions import HTTPError

from alpaca.common.enums import BaseURL
from alpaca.common.exceptions import APIError
from alpaca.common.rest import RESTClient


class LogoClient(RESTClient):
    """
    The REST client for Alpaca company logo images.

    Responses are ``image/png`` bytes. There is no JSON response model.
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
        Instantiates a Logo Client.

        Args:
            api_key (Optional[str], optional): Alpaca API key. Defaults to None.
            secret_key (Optional[str], optional): Alpaca API secret key. Defaults to None.
            oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.
            use_basic_auth (bool, optional): If true, API requests will use basic authorization headers.
            raw_data (bool, optional): Unused. Logo responses are always raw bytes.
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

    def get_logo(self, symbol: str, placeholder: Optional[bool] = None) -> bytes:
        """Returns the company logo for ``symbol`` as PNG bytes.

        Args:
            symbol (str): The ticker identifier used in the request path.
            placeholder (Optional[bool]): When false, omit the placeholder image if no logo exists.
                When omitted, the server default (true) applies.

        Returns:
            bytes: The PNG image.
        """
        params = None
        if placeholder is not None:
            params = {"placeholder": str(placeholder).lower()}

        url = self._base_url + "/" + self._api_version + "/logos/" + symbol
        response = self._session.get(
            url=url,
            params=params,
            headers=self._get_default_headers(),
        )
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            raise APIError(response.text, http_error)

        return response.content
