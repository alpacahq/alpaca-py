from typing import List

from alpaca.broker.client import BrokerClient
from alpaca.common.enums import BaseURL
from alpaca.trading.models import Calendar, Clock
from alpaca.trading.requests import GetCalendarRequest


def test_get_calendar(reqmock, client: BrokerClient):
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/calendar",
        text="""
        [
          {
            "date": "2022-05-16",
            "open": "09:30",
            "close": "16:00",
            "session_open": "0400",
            "session_close": "2000"
          },
          {
            "date": "2022-05-17",
            "open": "09:30",
            "close": "16:00",
            "session_open": "0400",
            "session_close": "2000"
          }
        ]
        """,
    )

    start = "2022-05-16"
    end = "2022-05-17"

    result = client.get_calendar(
        GetCalendarRequest(
            start=start,
            end=end,
        )
    )

    assert reqmock.called_once
    assert reqmock.request_history[0].qs == {"start": [start], "end": [end]}

    assert isinstance(result, List)
    assert len(result) == 2
    assert isinstance(result[0], Calendar)


def test_get_clock(reqmock, client: BrokerClient):
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/clock",
        text="""
        {
          "timestamp": "2022-05-16T16:32:24.14373588-04:00",
          "is_open": false,
          "next_open": "2022-05-17T09:30:00-04:00",
          "next_close": "2022-05-17T16:00:00-04:00"
        }
        """,
    )

    result = client.get_clock()

    assert reqmock.called_once
    assert isinstance(result, Clock)
