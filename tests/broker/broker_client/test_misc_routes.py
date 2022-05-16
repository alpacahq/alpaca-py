from typing import List

from alpaca.broker.client import BrokerClient
from alpaca.broker.models import GetCalendarRequest
from alpaca.common.enums import BaseURL
from alpaca.common.models import Calendar


def test_get_calendar(reqmock, client: BrokerClient):
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/calendar",
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
