from alpaca.common.models import Clock
from datetime import datetime


def test_clock_validates_timestamp():
    """Tests whether timestamp string is successfully parsed into datetime"""
    clock = Clock(
        timestamp="2022-04-28T14:07:04.451420928-04:00",
        is_open=True,
        next_open="2022-04-29T09:30:00-04:00",
        next_close="2022-04-28T16:00:00-04:00",
    )

    assert type(clock.timestamp) is datetime

    assert clock.timestamp.day == 28
