import json
from typing import Any, Dict, List, Union
from pydantic import BaseModel, TypeAdapter, ValidationError
from requests.exceptions import HTTPError
from requests import Request, Response


class ErrorBody(BaseModel):
    """
    Represent the body of an API error response.
    """

    code: int
    message: str


class PDTErrorBody(ErrorBody):
    """
    Represent the body of the API error in case of PDT.
    """

    day_trading_buying_power: float
    max_dtbp_used: float
    max_dtbp_used_so_far: float
    open_orders: int
    symbol: str


class BuyingPowerErrorBody(ErrorBody):
    """
    Represent the body of the API error in case of insufficient buying power.
    """

    buying_power: float
    cost_basis: float


class APIError(Exception):
    """
    Represent API related error coming from an HTTP request to one of Alpaca's APIs.

    Attributes:
        request (Request): will be the HTTP request.
        response (Response): will be the HTTP response.
        status_code (int): will be the HTTP status_code.
        body (Union[ErrorBody, Dict[str, Any]]): will have the body of the response,
            it will be a base model or the raw data if the pydantic validation fails.
        code (int): will be the Alpaca error code from the response body.
    """

    def __init__(
        self,
        http_error: HTTPError,
    ) -> None:
        super().__init__(http_error)
        self._http_error = http_error

    @property
    def request(self) -> Request:
        assert isinstance(self._http_error.request, Request)
        return self._http_error.request

    @property
    def response(self) -> Response:
        assert isinstance(self._http_error.response, Response)
        return self._http_error.response

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def body(self) -> Union[ErrorBody, Dict[str, Any]]:
        _body: Dict[str, Any] = json.loads(self.response.content)
        _models: List[ErrorBody] = [
            ErrorBody,
            BuyingPowerErrorBody,
            PDTErrorBody,
        ]
        for base_model in _models:
            if set(base_model.model_fields.keys()) == set(_body.keys()):
                try:
                    return TypeAdapter(base_model).validate_python(_body)
                except ValidationError:
                    return _body
        return _body

    @property
    def code(self) -> int:
        if isinstance(self.body, ErrorBody):
            return self.body.code
        elif isinstance(self.body, dict):
            return int(self.body.get("code"))
        else:
            return int(json.loads(self.response.content)["code"])


class RetryException(Exception):
    """
    Thrown by RESTClient's internally to represent a request that should be retried.
    """

    pass
