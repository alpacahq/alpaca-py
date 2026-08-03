import re
import platform

from requests_mock import Mocker

from alpaca import __version__
from alpaca.common.enums import BaseURL
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
