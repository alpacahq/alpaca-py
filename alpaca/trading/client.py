from uuid import UUID
from pydantic import parse_obj_as
from alpaca.broker.client import validate_uuid_id_param
from alpaca.common.rest import RESTClient
from typing import Optional, List, Union
from alpaca.common.enums import BaseURL
from alpaca.common.models import Order
from .models import (
    OrderRequest,
    GetOrdersRequest,
    ReplaceOrderRequest,
    GetOrderByIdRequest,
    CancelOrderResponse,
)
from ..common import APIError


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

        cancel_data = {"id": order_id}

        # handle error responses so that we can return it to the user
        try:
            response = self.delete(f"/orders/{order_id}")
            cancel_data["status"] = response.status_code
        except APIError as error:
            cancel_data["status"] = error.status_code

        return CancelOrderResponse(**cancel_data)
