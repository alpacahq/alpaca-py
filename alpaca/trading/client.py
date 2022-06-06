from uuid import UUID
from pydantic import parse_obj_as
from requests import HTTPError

from alpaca.broker.client import validate_uuid_id_param, validate_symbol_or_asset_id
from alpaca.common.rest import RESTClient
from typing import Optional, List, Union
from alpaca.common.enums import BaseURL
from alpaca.common.models import (
    Order,
    Clock,
    Calendar,
    GetCalendarRequest,
    Position,
    ClosePositionResponse,
    ClosePositionRequest,
    Asset,
    GetAssetsRequest,
)
from .models import (
    OrderRequest,
    GetOrdersRequest,
    ReplaceOrderRequest,
    GetOrderByIdRequest,
    CancelOrderResponse,
)


class TradingClient(RESTClient):
    """
    A client to interact with the trading API, in both paper and live mode.
    """

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

    # ############################## ORDERS ################################# #

    def submit_order(self, order_data: OrderRequest) -> Order:
        """Creates an order to buy or sell an asset.

        Args:
            order_data (OrderCreationRequest): The request data for creating a new order.

        Returns:
            Order: The resulting submitted order.
        """
        data = order_data.to_request_fields()
        response = self.post("/orders", data)

        return Order(**response)

    def get_orders(self, filter: Optional[GetOrdersRequest] = None) -> List[Order]:
        """
        Returns all orders. Orders can be filtered by parameters.

        Args:
            filter (Optional[GetOrdersRequest]): The parameters to filter the orders with.

        Returns:
            List[Order]: The queried orders.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        if "symbols" in params and type(params["symbols"]) is List:
            params["symbols"] = ",".join(params["symbols"])

        response = self.get("/orders", params)

        return parse_obj_as(List[Order], response)

    def get_order_by_id(
        self, order_id: Union[UUID, str], filter: Optional[GetOrderByIdRequest] = None
    ) -> Order:
        """
        Returns a specific order by its order id.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier for the order.
            filter (Optional[GetOrderByIdRequest]): The parameters for the query.

        Returns:
            Order: The order that was queried.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        order_id = validate_uuid_id_param(order_id, "order_id")

        response = self.get(f"/orders/{order_id}", params)

        return Order(**response)

    def get_order_by_client_id(self, client_id: Union[UUID, str]) -> Order:
        """
        Returns a specific order by its client order id.

        Args:
            client_id (Union[UUID, str]): The unique client order id identifier for the order.

        Returns:
            Order: The queried order.
        """
        client_id = validate_uuid_id_param(client_id, "client_id")

        response = self.get(f"/orders/{client_id}")

        return Order(**response)

    def replace_order(
        self,
        order_id: Union[UUID, str],
        order_data: Optional[ReplaceOrderRequest] = None,
    ) -> Order:
        """
        Updates an order with new parameters.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier for the order being replaced.
            order_data (Optional[ReplaceOrderRequest]): The parameters we wish to update.

        Returns:
            Order: The updated order.
        """
        # checking to see if we specified at least one param
        params = order_data.to_request_fields() if order_data is not None else {}

        order_id = validate_uuid_id_param(order_id, "order_id")

        response = self.patch(f"/orders/{order_id}", params)

        return Order(**response)

    def cancel_orders(self) -> List[CancelOrderResponse]:
        """
        Cancels all orders.

        Returns:
            List[CancelOrderResponse]: The list of HTTP statuses for each order attempted to be cancelled.
        """
        response = self.delete(f"/orders")

        return parse_obj_as(List[CancelOrderResponse], response)

    def cancel_order_by_id(self, order_id: Union[UUID, str]) -> CancelOrderResponse:
        """
        Cancels a specific order by its order id.

        Args:
            order_id (Union[UUID, str]): The unique uuid identifier of the order being cancelled.

        Returns:
            CancelOrderResponse: The HTTP response from the cancel request.
        """
        order_id = validate_uuid_id_param(order_id, "order_id")
        status_code: Optional[int] = None

        # We are making a direct HTTP call without using base class
        # The _one_request method returns a NoneType for empty responses
        # We need to capture the HTTP status code for empty responses
        target_url = f"{self._base_url}/{self._api_version}/orders/{order_id}"
        num_tries = 0

        while num_tries <= self._retry:
            response = self._session.delete(
                url=target_url,
                headers=self._get_default_headers(),
                allow_redirects=True,
                stream=True,
            )
            num_tries += 1
            try:
                response.raise_for_status()
                status_code = response.status_code
            except HTTPError as http_error:
                if response.status_code in self._retry_codes:
                    continue

                if "code" in response.text:
                    error = response.json()
                    if "code" in error:
                        status_code = error["code"]
                else:
                    raise http_error

            # if we got here there were no issues', so status_code is now a value
            break

        return CancelOrderResponse(id=order_id, status=status_code)

    # ############################## POSITIONS ################################# #

    def get_all_positions(
        self,
    ) -> List[Position]:
        """
        Gets all the current open positions.

        Returns:
            List[Position]: List of open positions.
        """
        response = self.get("/positions")
        return parse_obj_as(List[Position], response)

    def get_open_position(self, symbol_or_asset_id: Union[UUID, str]) -> Position:
        """
        Gets the open position for an account for a single asset.

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to get.

        Returns:
            Position: Open position of the asset.
        """
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.get(f"/positions/{symbol_or_asset_id}")
        return Position(**response)

    def close_all_positions(self, cancel_orders: bool) -> List[ClosePositionResponse]:
        """
        Liquidates all positions for an account.

        Places an order for each open position to liquidate.

        Args:
            cancel_orders (bool): If true is specified, cancel all open orders before liquidating all positions.

        Returns:
            List[ClosePositionResponse]: A list of responses from each closed position containing the status code and
              order id.
        """
        response = self.delete(
            "/positions",
            {"cancel_orders": cancel_orders},
        )
        return parse_obj_as(List[ClosePositionResponse], response)

    def close_position(
        self,
        symbol_or_asset_id: Union[UUID, str],
        close_options: Optional[ClosePositionRequest] = None,
    ) -> Order:
        """
        Liquidates the position for a single asset.

        Places a single order to close the position for the asset.

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol name of asset id of the position to close.
            close_options: The various close position request parameters.

        Returns:
            Order: The order that was placed to close the position.
        """
        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)
        response = self.delete(
            f"/positions/{symbol_or_asset_id}",
            close_options.to_request_fields() if close_options else {},
        )
        return Order(**response)

    # ############################## Assets ################################# #

    def get_all_assets(self, filter: Optional[GetAssetsRequest] = None) -> List[Asset]:
        """
        The assets API serves as the master list of assets available for trade and data consumption from Alpaca.
        Some assets are not tradable with Alpaca. These assets will be marked with the flag tradable=false.

        Args:
            filter (Optional[GetAssetsRequest]): The parameters that can be assets can be queried by.

        Returns:
            List[Asset]: The list of assets.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter is not None else {}

        response = self.get(f"/assets", params)

        return parse_obj_as(List[Asset], response)

    def get_asset(self, symbol_or_asset_id: Union[UUID, str]) -> Asset:
        """
        Returns a specific asset by its symbol or asset id. If the specified asset does not exist
        a 404 error will be thrown.

        Args:
            symbol_or_asset_id (Union[UUID, str]): The symbol or asset id for the specified asset

        Returns:
            Asset: The asset if it exists.
        """

        symbol_or_asset_id = validate_symbol_or_asset_id(symbol_or_asset_id)

        response = self.get(f"/assets/{symbol_or_asset_id}")

        return Asset(**response)

    # ############################## CLOCK & CALENDAR ################################# #

    def get_clock(self) -> Clock:
        """
        Gets the current market timestamp, whether or not the market is currently open, as well as the times
        of the next market open and close.

        Returns:
            Clock: The market Clock data
        """
        return Clock(**self.get("/clock"))

    def get_calendar(
        self,
        filters: Optional[GetCalendarRequest] = None,
    ) -> List[Calendar]:
        """
        The calendar API serves the full list of market days from 1970 to 2029. It can also be queried by specifying a
        start and/or end time to narrow down the results.

        In addition to the dates, the response also contains the specific open and close times for the market days,
        taking into account early closures.

        Args:
            filters: Any optional filters to limit the returned market days

        Returns:
            List[Calendar]: A list of Calendar objects representing the market days.
        """

        result = self.get(
            "/calendar", filters.to_request_fields() if filters is not None else {}
        )

        return parse_obj_as(List[Calendar], result)
