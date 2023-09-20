import json
from typing import Optional
from pydantic import BaseModel, TypeAdapter
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


class APIError(Exception):
    """
    Represent API related error.
    error.status_code will have http status code.
    """

    def __init__(
        self,
        error: str,
        http_error: Optional[HTTPError] = None,
    ):
        super().__init__(error)
        self._error = error
        self._http_error = http_error

    @property
    def code(self) -> str:
        error = json.loads(self._error)
        return error["code"]

    @property
    def status_code(self) -> int:
        http_error = self._http_error
        if http_error is not None and hasattr(http_error, "response"):
            return http_error.response.status_code

    @property
    def request(self) -> Optional[Request]:
        if self._http_error is not None:
            return self._http_error.request

    @property
    def response(self)  -> Optional[Response]:
        if self._http_error is not None:
            return self._http_error.response

    @property
    def body(self)  -> Optional[ErrorBody]:
        error = json.loads(self._error)
        try:
            return TypeAdapter(PDTErrorBody).validate_python(error)
        except Exception:
            return None


class RetryException(Exception):
    """
    Thrown by RESTClient's internally to represent a request that should be retried.
    """

    pass
