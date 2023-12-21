import json


class APIError(Exception):
    """
    Represent API related error.
    error.status_code will have http status code.
    """

    def __init__(self, error, http_error=None):
        detailed_error = {
            "payload": error,
        }

        if http_error is not None:
            if hasattr(http_error, "response"):
                detailed_error["status_code"] = http_error.response.status_code
                detailed_error["reason"] = http_error.response.reason
            if hasattr(http_error, "request"):
                detailed_error["method"] = http_error.request.method
                detailed_error["url"] = http_error.request.url
            # add tips for auth key error
            if detailed_error["status_code"] in [401, 403]:
                detailed_error[
                    "tips"
                ] = "please check your API key and environment (paper/sandbox/live)"

        self._error = error
        self._http_error = http_error
        super().__init__(detailed_error)

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
