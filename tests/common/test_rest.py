import re
import platform

import pytest
from requests_mock import Mocker

from alpaca import __version__
from alpaca.common.constants import DEFAULT_RETRY_ATTEMPTS, DEFAULT_RETRY_WAIT_SECONDS
from alpaca.common.enums import BaseURL
from alpaca.common.exceptions import APIError
from alpaca.common.utils import get_default_user_agent
from alpaca.trading.client import TradingClient

USER_AGENT_RE = re.compile(r"^APCA-PY/[^\s]+ Python/[^\s]+$")


def test_get_default_user_agent_format():
    """The User-Agent must follow APCA-<PLATFORM>/<sdk-version> <Runtime>/<runtime-version>."""

    user_agent = get_default_user_agent()

    assert USER_AGENT_RE.match(user_agent)
    assert user_agent == f"APCA-PY/{__version__} Python/{platform.python_version()}"


def test_rest_client_default_headers_include_user_agent(trading_client: TradingClient):
    headers = trading_client._get_default_headers()

    assert headers["User-Agent"] == get_default_user_agent()


def test_request_sends_user_agent_header(
    reqmock: Mocker, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/clock",
        text="""
        {
          "timestamp": "2022-04-28T14:07:04.451420928-04:00",
          "is_open": true,
          "next_open": "2022-04-29T09:30:00-04:00",
          "next_close": "2022-04-28T16:00:00-04:00"
        }
        """,
    )

    trading_client.get_clock()

    assert reqmock.called_once
    assert reqmock.last_request.headers["User-Agent"] == get_default_user_agent()


def test_request_retries_rate_limited_response(
    reqmock: Mocker, trading_client: TradingClient, monkeypatch
):
    """A 429 (Rate Limit) response is retried by default instead of raised."""
    sleeps = []
    monkeypatch.setattr(
        "alpaca.common.rest.time.sleep", lambda seconds: sleeps.append(seconds)
    )
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/clock",
        [
            {"status_code": 429, "text": '{"message": "rate limit exceeded"}'},
            {
                "status_code": 200,
                "text": """
                {
                  "timestamp": "2022-04-28T14:07:04.451420928-04:00",
                  "is_open": true,
                  "next_open": "2022-04-29T09:30:00-04:00",
                  "next_close": "2022-04-28T16:00:00-04:00"
                }
                """,
            },
        ],
    )

    clock = trading_client.get_clock()

    assert reqmock.call_count == 2
    assert clock.is_open
    # Confirms the retry loop actually waits between attempts, not just that
    # it retries.
    assert sleeps == [DEFAULT_RETRY_WAIT_SECONDS]


def test_request_raises_after_exhausting_retries(
    reqmock: Mocker, trading_client: TradingClient, monkeypatch
):
    """If every attempt is rate limited, the client gives up and raises APIError
    instead of retrying forever."""
    monkeypatch.setattr("alpaca.common.rest.time.sleep", lambda seconds: None)
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/clock",
        status_code=429,
        text='{"message": "rate limit exceeded"}',
    )

    with pytest.raises(APIError):
        trading_client.get_clock()

    # One initial attempt plus one retry per configured retry attempt.
    assert reqmock.call_count == DEFAULT_RETRY_ATTEMPTS + 1
