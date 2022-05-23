from alpaca.common.rest import RESTClient
from typing import Optional
from alpaca.common.enums import BaseURL
from alpaca.common.models import Order
from .models import OrderCreationRequest


class TradingClient(RESTClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        sandbox: bool = True,
        raw_data: bool = False,
        url_override: Optional[str] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            oauth_token=oauth_token,
            api_version="v2",
            base_url=url_override
            if url_override
            else BaseURL.TRADING_PAPER
            if sandbox
            else BaseURL.TRADING_LIVE,
            sandbox=sandbox,
            raw_data=raw_data,
        )

    def submit_order(self, order_data: OrderCreationRequest) -> Order:
        """ """
        data = order_data.to_request_fields()
        response = self.post("/orders", data)

        return Order(**response)
