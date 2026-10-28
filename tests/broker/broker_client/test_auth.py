import base64

import pytest

from alpaca.broker.client import BrokerClient
from alpaca.common.enums import BaseURL
from alpaca.trading.models import Clock

CLOCK_RESPONSE = """
{
  "timestamp": "2022-05-16T16:32:24.14373588-04:00",
  "is_open": false,
  "next_open": "2022-05-17T09:30:00-04:00",
  "next_close": "2022-05-17T16:00:00-04:00"
}
"""


def test_oauth_token_uses_bearer_header(reqmock):
    client = BrokerClient(oauth_token="test-oauth-token", sandbox=True)
    reqmock.get(f"{BaseURL.BROKER_SANDBOX.value}/v1/clock", text=CLOCK_RESPONSE)

    result = client.get_clock()

    assert reqmock.called_once
    assert reqmock.last_request.headers["Authorization"] == "Bearer test-oauth-token"
    assert isinstance(result, Clock)


def test_basic_auth_still_default(reqmock):
    client = BrokerClient("key-id", "secret-key", sandbox=True)
    reqmock.get(f"{BaseURL.BROKER_SANDBOX.value}/v1/clock", text=CLOCK_RESPONSE)

    client.get_clock()

    expected = base64.b64encode(b"key-id:secret-key").decode("utf-8")
    assert reqmock.last_request.headers["Authorization"] == "Basic " + expected


def test_oauth_token_and_keys_are_mutually_exclusive():
    with pytest.raises(ValueError):
        BrokerClient("key-id", "secret-key", oauth_token="test-oauth-token")
