import json


class APIError(Exception):
    """
    Represent API related error.
    error.status_code will have http status code.
    """

    def __init__(self, error, http_error=None):
        super().__init__(error)
        self._error = error
        self._http_error = http_error

    @property
    def code(self):
        error = json.loads(self._error)
        return error["code"]

    @property
    def status_code(self):
        http_error = self._http_error
        if http_error is not None and hasattr(http_error, "response"):
            return http_error.response.status_code

    @property
    def request(self):
        if self._http_error is not None:
            return self._http_error.request

    @property
    def response(self):
        if self._http_error is not None:
            return self._http_error.response


class RetryException(Exception):
    """
    Thrown by RESTClient's internally to represent a request that should be retried.
    """

    pass
